"""Local authentication: SQLite user store + opaque bearer tokens.

Users are stored in backend/runtime/users.db (gitignored). Deleting that
file resets all accounts. Tokens are random opaque strings with a 7-day
expiry, stored in the sessions table so logout can revoke them.
"""

import hashlib
import hmac
import re
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

DB_PATH = Path(__file__).resolve().parent / "runtime" / "users.db"
TOKEN_TTL_DAYS = 7
PBKDF2_ITERATIONS = 200_000
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


def _validate_password(password: str) -> Optional[str]:
    """Return an error message when the password fails the complexity rules.

    Length 8-128 and must contain at least one letter and one digit.
    """
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        return (
            f"密码长度需为 {PASSWORD_MIN_LENGTH}-{PASSWORD_MAX_LENGTH} 位，"
            "且同时包含字母和数字"
        )
    if not re.search(r"[A-Za-z]", password):
        return "密码需同时包含字母和数字（当前缺少字母）"
    if not re.search(r"\d", password):
        return "密码需同时包含字母和数字（当前缺少数字）"
    return None


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def _db() -> Iterator[sqlite3.Connection]:
    """Open a fresh connection, commit on success, close afterwards.

    A new connection per request avoids SQLite cross-thread issues.
    """
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _init_db() -> None:
    with _db() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT,
                expires_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
            """
        )


_init_db()


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PBKDF2_ITERATIONS,
    )
    return f"{salt}${dk.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, expected = stored.split("$", 1)
    except ValueError:
        return False

    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PBKDF2_ITERATIONS,
    )
    return hmac.compare_digest(dk.hex(), expected)


def _issue_token(db: sqlite3.Connection, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=TOKEN_TTL_DAYS)
    db.execute(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, datetime.now(timezone.utc).isoformat(), expires_at.isoformat()),
    )
    return token


def _get_user_by_token(
    db: sqlite3.Connection, token: str
) -> Optional[Dict[str, Any]]:
    row = db.execute(
        """
        SELECT users.id, users.username, users.email, users.created_at,
               sessions.expires_at
        FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.token = ?
        """,
        (token,),
    ).fetchone()

    if row is None:
        return None

    try:
        expires_at = datetime.fromisoformat(row["expires_at"])
    except (ValueError, TypeError):
        return None

    if expires_at < datetime.now(timezone.utc):
        db.execute("DELETE FROM sessions WHERE token = ?", (token,))
        return None

    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "created_at": row["created_at"],
    }


bearer_scheme = HTTPBearer(auto_error=False)


def _extract_token(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供登录凭证",
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录凭证格式错误",
        )

    return credentials.credentials


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> Dict[str, Any]:
    """Verify the Bearer token against the local sessions table."""
    token = _extract_token(credentials)

    with _db() as db:
        user = _get_user_by_token(db, token)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录凭证无效或已过期",
        )

    return user


router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    identifier: str
    password: str


@router.post("/register")
def register(req: RegisterRequest) -> Dict[str, Any]:
    username = req.username.strip()
    email = req.email.strip().lower()
    password = req.password

    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    if len(username) > 30:
        raise HTTPException(status_code=400, detail="用户名长度不能超过 30 位")
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    password_error = _validate_password(password)
    if password_error:
        raise HTTPException(status_code=400, detail=password_error)

    password_hash = _hash_password(password)

    with _db() as db:
        exists = db.execute(
            "SELECT 1 FROM users WHERE lower(username) = lower(?) OR email = ?",
            (username, email),
        ).fetchone()
        if exists:
            raise HTTPException(
                status_code=400, detail="用户名或邮箱已存在"
            )

        try:
            cur = db.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=400, detail="用户名或邮箱已存在"
            )

        user_id = cur.lastrowid
        token = _issue_token(db, user_id)

        user_row = db.execute(
            "SELECT id, username, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    return {"token": token, "user": dict(user_row)}


@router.post("/login")
def login(req: LoginRequest) -> Dict[str, Any]:
    identifier = req.identifier.strip()

    if not identifier:
        raise HTTPException(status_code=400, detail="请输入用户名或邮箱")

    with _db() as db:
        row = db.execute(
            """
            SELECT id, username, email, password_hash, created_at
            FROM users
            WHERE lower(username) = lower(?) OR lower(email) = lower(?)
            """,
            (identifier, identifier),
        ).fetchone()

        if row is None or not _verify_password(req.password, row["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
            )

        token = _issue_token(db, row["id"])

    user = {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "created_at": row["created_at"],
    }

    return {"token": token, "user": user}


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> Dict[str, Any]:
    token = _extract_token(credentials)

    with _db() as db:
        db.execute("DELETE FROM sessions WHERE token = ?", (token,))

    return {"message": "登出成功"}


@router.get("/me")
def me(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return user
