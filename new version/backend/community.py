"""Open-source community: shared projects, posts, likes, favorites, comments, follows.

Community data lives in the same SQLite store as auth (backend/runtime/users.db),
so shared projects and posts are visible to every logged-in user — the product
grows from a private tool into an open-source-style community.

Deleting users.db resets accounts AND community content.
"""

import json
import os
import sqlite3
import tempfile
import zipfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from starlette.background import BackgroundTask

from auth import DB_PATH, _db as auth_db, _get_user_by_token, get_current_user
from llm import call_doubao

PHASE_DATA_MAX_BYTES = 2 * 1024 * 1024
PAGE_SIZE = 20
MAX_COMMENT_LENGTH = 2000

# 项目分类(两级:科室大类 + 术式小类,分享表单与筛选条联动选择)。
# 大类按医院外科科室划分,小类为各科室常见术式,以后新增术式只需在对应科室的 items 里加一项。
CATEGORY_GROUPS = [
    {
        "name": "普通外科",
        "items": ["阑尾切除术", "疝修补术", "肛肠手术", "体表肿物切除术", "腹腔探查术"],
    },
    {
        "name": "胃肠外科",
        "items": ["胃切除术", "结直肠手术", "消化道穿孔修补术", "肠梗阻手术", "减重代谢手术"],
    },
    {
        "name": "肝胆外科",
        "items": ["胆囊切除术", "肝切除术", "胆管手术", "胰腺手术", "脾脏手术"],
    },
    {
        "name": "甲状腺乳腺外科",
        "items": ["甲状腺手术", "甲状腺癌根治术", "乳腺手术", "乳腺癌改良根治术", "保乳手术"],
    },
    {
        "name": "心胸外科",
        "items": [
            "冠状动脉搭桥术",
            "心脏瓣膜手术",
            "先天性心脏病矫治术",
            "主动脉手术",
            "肺切除术",
            "食管手术",
            "胸腔镜手术",
        ],
    },
    {
        "name": "血管外科",
        "items": ["动脉搭桥手术", "动脉取栓手术", "大隐静脉手术", "深静脉血栓手术", "血管支架植入术"],
    },
    {
        "name": "泌尿外科",
        "items": ["泌尿系结石手术", "膀胱手术", "前列腺手术", "前列腺癌根治术", "肾脏手术", "包皮环切术"],
    },
    {
        "name": "骨科",
        "items": ["骨折内固定手术", "关节置换手术", "关节镜手术", "脊柱手术", "骨肿瘤手术"],
    },
    {
        "name": "神经外科",
        "items": ["开颅手术", "颅脑肿瘤手术", "脑血管手术", "脑出血手术", "脊柱脊髓手术"],
    },
    {
        "name": "妇科",
        "items": ["子宫切除术", "卵巢囊肿剥除术", "子宫肌瘤剔除术", "宫腔镜手术", "腹腔镜妇科手术"],
    },
    {
        "name": "眼科",
        "items": ["白内障手术", "青光眼手术", "眼底手术", "眼整形手术"],
    },
    {
        "name": "耳鼻喉科",
        "items": ["扁桃体手术", "鼻内镜手术", "耳部手术", "喉部手术", "鼾症手术"],
    },
    {
        "name": "口腔颌面外科",
        "items": ["颌骨手术", "腮腺手术", "口腔肿瘤手术", "唇腭裂手术", "种植牙手术"],
    },
    {
        "name": "小儿外科",
        "items": ["新生儿外科手术", "小儿疝手术", "先天性畸形矫治术", "小儿泌尿手术"],
    },
    {
        "name": "整形外科",
        "items": ["烧伤整形手术", "瘢痕修复手术", "美容整形手术", "皮瓣移植手术", "吸脂塑形手术"],
    },
    {
        "name": "器官移植科",
        "items": ["肝移植手术", "肾移植手术", "心脏移植手术", "肺移植手术"],
    },
    {
        "name": "创伤外科",
        "items": ["多发伤急救手术", "四肢创伤手术", "骨盆创伤手术", "胸腹联合伤手术", "开放性骨折手术"],
    },
    {
        "name": "其他",
        "items": ["其他"],
    },
]


def _category_group_of(subcategory: str) -> Optional[str]:
    """小类名 → 所属大类名;不在任何大类里则返回 None。"""
    for group in CATEGORY_GROUPS:
        if subcategory in group["items"]:
            return group["name"]
    return None


def _valid_category(category: str, subcategory: str) -> bool:
    """校验 category(大类) + subcategory(小类) 组合是否合法。"""
    if not category:
        return True
    for group in CATEGORY_GROUPS:
        if group["name"] == category:
            return not subcategory or subcategory in group["items"]
    return False

VIDEO_DIR = Path(__file__).resolve().parent / "runtime" / "videos"
VIDEO_MAX_BYTES = 1024 * 1024 * 1024  # 1GB
VIDEO_CHUNK_SIZE = 1024 * 1024


@contextmanager
def _db() -> Iterator[sqlite3.Connection]:
    """Fresh connection per request, commit on success, close afterwards.

    Same pattern as auth._db(); community tables additionally enforce
    foreign keys so orphan rows can never survive a user deletion.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
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
            CREATE TABLE IF NOT EXISTS community_projects (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title       TEXT NOT NULL,
                procedure   TEXT DEFAULT '',
                surgeon     TEXT DEFAULT '',
                department  TEXT DEFAULT '',
                date        TEXT DEFAULT '',
                duration    TEXT DEFAULT '',
                description TEXT DEFAULT '',
                file_name   TEXT DEFAULT '',
                status      TEXT DEFAULT '分析完成',
                phase_data  TEXT DEFAULT '',
                summary     TEXT DEFAULT '',
                created_at  TEXT DEFAULT (datetime('now')),
                updated_at  TEXT DEFAULT (datetime('now'))
            )
            """
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_projects_created ON community_projects (created_at DESC)"
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_projects_user ON community_projects (user_id)"
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title      TEXT NOT NULL,
                content    TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_posts_created ON posts (created_at DESC)"
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS comments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                target_type TEXT NOT NULL CHECK (target_type IN ('project','post')),
                target_id   INTEGER NOT NULL,
                content     TEXT NOT NULL,
                parent_id   INTEGER REFERENCES comments(id) ON DELETE CASCADE,
                created_at  TEXT DEFAULT (datetime('now'))
            )
            """
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_comments_target ON comments (target_type, target_id)"
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS likes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                target_type TEXT NOT NULL CHECK (target_type IN ('project','post')),
                target_id   INTEGER NOT NULL,
                created_at  TEXT DEFAULT (datetime('now')),
                UNIQUE (user_id, target_type, target_id)
            )
            """
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_likes_target ON likes (target_type, target_id)"
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS favorites (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                target_type TEXT NOT NULL CHECK (target_type IN ('project','post')),
                target_id   INTEGER NOT NULL,
                created_at  TEXT DEFAULT (datetime('now')),
                UNIQUE (user_id, target_type, target_id)
            )
            """
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_favorites_target ON favorites (target_type, target_id)"
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS follows (
                follower_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                followee_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at  TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (follower_id, followee_id),
                CHECK (follower_id != followee_id)
            )
            """
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_follows_followee ON follows (followee_id)"
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS downloads (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                project_id INTEGER NOT NULL REFERENCES community_projects(id) ON DELETE CASCADE,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE (user_id, project_id)
            )
            """
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_downloads_user ON downloads (user_id)"
        )

        # 用户反馈:type 反馈类型,status 处理状态,reply 管理员回复(暂由平台方在库中维护)
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                type TEXT DEFAULT '功能建议',
                content TEXT NOT NULL,
                status TEXT DEFAULT '待处理',
                reply TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback (user_id)"
        )

        # Migration: shared videos live on the filesystem, DB only keeps the
        # original file name. CREATE TABLE IF NOT EXISTS can't add columns to
        # an existing table, so migrate explicitly.
        cols = [row[1] for row in db.execute("PRAGMA table_info(community_projects)")]
        if "video_file_name" not in cols:
            db.execute(
                "ALTER TABLE community_projects ADD COLUMN video_file_name TEXT DEFAULT ''"
            )

        comment_cols = [row[1] for row in db.execute("PRAGMA table_info(comments)")]
        if "parent_id" not in comment_cols:
            db.execute(
                "ALTER TABLE comments ADD COLUMN parent_id INTEGER "
                "REFERENCES comments(id) ON DELETE CASCADE"
            )

        # 项目分类:存量项目都是胆囊切除术,统一回填
        if "category" not in cols:
            db.execute(
                "ALTER TABLE community_projects ADD COLUMN category TEXT DEFAULT ''"
            )
        db.execute(
            "UPDATE community_projects SET category = '胆囊切除术' WHERE category = ''"
        )

        # 两级分类:category 存大类,subcategory 存小类。
        # 迁移规则:有小类且小类在分组里 → 按当前分组重归大类(分组调整后自动跟随);
        # 只有分类且分类是小类名(旧版扁平数据)→ 归入对应大类。
        cols = [row[1] for row in db.execute("PRAGMA table_info(community_projects)")]
        if "subcategory" not in cols:
            db.execute(
                "ALTER TABLE community_projects ADD COLUMN subcategory TEXT DEFAULT ''"
            )
        for row in db.execute(
            "SELECT id, category, subcategory FROM community_projects WHERE category != ''"
        ):
            cat = row["category"] or ""
            sub = row["subcategory"] or ""
            if sub:
                group_name = _category_group_of(sub)
                if group_name and group_name != cat:
                    db.execute(
                        "UPDATE community_projects SET category = ? WHERE id = ?",
                        (group_name, row["id"]),
                    )
            else:
                group_name = _category_group_of(cat)
                if group_name:
                    db.execute(
                        "UPDATE community_projects SET category = ?, subcategory = ? WHERE id = ?",
                        (group_name, cat, row["id"]),
                    )


_init_db()

router = APIRouter(prefix="/api/community", tags=["community"])


def _check_target_type(target_type: str) -> None:
    if target_type not in ("project", "post"):
        raise HTTPException(status_code=400, detail="target_type 只能是 project 或 post")


def _target_exists(db: sqlite3.Connection, target_type: str, target_id: int) -> bool:
    table = "community_projects" if target_type == "project" else "posts"
    row = db.execute(f"SELECT 1 FROM {table} WHERE id = ?", (target_id,)).fetchone()
    return row is not None


def _require_target(db: sqlite3.Connection, target_type: str, target_id: int) -> None:
    if not _target_exists(db, target_type, target_id):
        label = "项目" if target_type == "project" else "帖子"
        raise HTTPException(status_code=404, detail=f"{label}不存在或已删除")


def _check_owner(user: Dict[str, Any], owner_id: int, label: str) -> None:
    if user["id"] != owner_id:
        raise HTTPException(status_code=403, detail=f"只能操作自己发布的{label}")


def _purge_target(db: sqlite3.Connection, target_type: str, target_id: int) -> None:
    """Delete likes/favorites/comments attached to a removed project or post."""
    for table in ("likes", "favorites", "comments"):
        db.execute(
            f"DELETE FROM {table} WHERE target_type = ? AND target_id = ?",
            (target_type, target_id),
        )


def _video_file(project_id: int, file_name: str) -> Path:
    """Filesystem path of a shared project video: runtime/videos/{id}{suffix}."""
    suffix = Path(file_name or "video.mp4").suffix or ".mp4"
    return VIDEO_DIR / f"{project_id}{suffix}"


def _remove_video_file(project_id: int, file_name: str) -> None:
    _video_file(project_id, file_name).unlink(missing_ok=True)


def _compute_summary(phase_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    result = (phase_data or {}).get("result") or {}
    meta = result.get("meta") or {}
    steps = result.get("steps") or []
    distribution = result.get("distribution") or []
    edited = (phase_data or {}).get("editedSegments") or []
    return {
        "stepCount": len(steps),
        "editedCount": len(edited),
        "durationSeconds": meta.get("durationSeconds"),
        "phaseLabels": [
            d.get("phaseLabel")
            for d in distribution
            if (d.get("seconds") or 0) > 0 and d.get("phaseLabel")
        ],
    }


def _store_phase_data(phase_data: Optional[Dict[str, Any]]) -> tuple:
    """Validate size and return (phase_data_json, summary_json)."""
    if phase_data is None:
        return "", "{}"
    try:
        raw = json.dumps(phase_data, ensure_ascii=False)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="分析数据格式不正确")
    if len(raw.encode("utf-8")) > PHASE_DATA_MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail="分析数据体积过大(超过 2MB)，请去掉逐帧预测数据后重试",
        )
    summary = _compute_summary(phase_data)
    return raw, json.dumps(summary, ensure_ascii=False)


def _engagement(
    db: sqlite3.Connection, user: Dict[str, Any], target_type: str, target_id: int
) -> Dict[str, Any]:
    """likeCount/favoriteCount/commentCount + current user's liked/favorited flags."""
    like_count = db.execute(
        "SELECT COUNT(*) FROM likes WHERE target_type = ? AND target_id = ?",
        (target_type, target_id),
    ).fetchone()[0]
    fav_count = db.execute(
        "SELECT COUNT(*) FROM favorites WHERE target_type = ? AND target_id = ?",
        (target_type, target_id),
    ).fetchone()[0]
    comment_count = db.execute(
        "SELECT COUNT(*) FROM comments WHERE target_type = ? AND target_id = ?",
        (target_type, target_id),
    ).fetchone()[0]
    liked = db.execute(
        "SELECT 1 FROM likes WHERE user_id = ? AND target_type = ? AND target_id = ?",
        (user["id"], target_type, target_id),
    ).fetchone() is not None
    favorited = db.execute(
        "SELECT 1 FROM favorites WHERE user_id = ? AND target_type = ? AND target_id = ?",
        (user["id"], target_type, target_id),
    ).fetchone() is not None
    return {
        "likeCount": like_count,
        "favoriteCount": fav_count,
        "commentCount": comment_count,
        "liked": liked,
        "favorited": favorited,
    }


def _parse_summary(raw: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(raw) if raw else {}
        return parsed if isinstance(parsed, dict) else {}
    except (ValueError, TypeError):
        return {}


def _project_card(db: sqlite3.Connection, row: sqlite3.Row, user: Dict[str, Any]) -> Dict[str, Any]:
    extra = _engagement(db, user, "project", row["id"])
    return {
        "id": row["id"],
        "title": row["title"],
        "category": row["category"] or "",
        "subcategory": row["subcategory"] or "",
        "procedure": row["procedure"],
        "surgeon": row["surgeon"],
        "department": row["department"],
        "date": row["date"],
        "duration": row["duration"],
        "description": row["description"],
        "fileName": row["file_name"],
        "status": row["status"],
        "author": {"id": row["user_id"], "username": row["username"]},
        "summary": _parse_summary(row["summary"]),
        "videoFileName": row["video_file_name"],
        "hasVideo": bool(row["video_file_name"]),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
        **extra,
    }


def _post_card(db: sqlite3.Connection, row: sqlite3.Row, user: Dict[str, Any]) -> Dict[str, Any]:
    extra = _engagement(db, user, "post", row["id"])
    content = row["content"] or ""
    return {
        "id": row["id"],
        "title": row["title"],
        "author": {"id": row["user_id"], "username": row["username"]},
        "excerpt": content[:120],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
        **extra,
    }


# ---------------------------------------------------------------- projects

@router.get("/categories")
def list_categories(
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """项目分类(两级:大类 + 小类,分享表单与筛选条联动选择,加新分类只需改 CATEGORY_GROUPS)。"""
    return {"groups": CATEGORY_GROUPS}


class ShareProjectRequest(BaseModel):
    title: str
    category: str = ""
    subcategory: str = ""
    procedure: str = ""
    surgeon: str = ""
    department: str = ""
    date: str = ""
    duration: str = ""
    description: str = ""
    fileName: str = ""
    status: str = "分析完成"
    phaseAnalysis: Optional[Dict[str, Any]] = None


@router.get("/projects")
def list_projects(
    q: str = "",
    sort: str = "newest",
    limit: int = PAGE_SIZE,
    offset: int = 0,
    mine: bool = False,
    author_id: Optional[int] = None,
    category: str = "",
    subcategory: str = "",
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    conditions: list = []
    params: list = []
    keyword = (q or "").strip()
    if keyword:
        like = f"%{keyword}%"
        conditions.append(
            "(p.title LIKE ? OR p.description LIKE ? OR p.procedure LIKE ? OR u.username LIKE ?)"
        )
        params += [like, like, like, like]
    if mine:
        conditions.append("p.user_id = ?")
        params.append(user["id"])
    if author_id is not None:
        conditions.append("p.user_id = ?")
        params.append(author_id)
    if category:
        conditions.append("p.category = ?")
        params.append(category)
        if subcategory:
            conditions.append("p.subcategory = ?")
            params.append(subcategory)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    if sort == "popular":
        order = (
            "(SELECT COUNT(*) FROM likes l WHERE l.target_type='project' AND l.target_id=p.id) DESC, "
            "p.created_at DESC"
        )
    else:
        order = "p.created_at DESC"

    with _db() as db:
        total = db.execute(
            f"SELECT COUNT(*) FROM community_projects p JOIN users u ON u.id = p.user_id {where}",
            params,
        ).fetchone()[0]
        rows = db.execute(
            f"""
            SELECT p.*, u.username
            FROM community_projects p JOIN users u ON u.id = p.user_id
            {where}
            ORDER BY {order}
            LIMIT ? OFFSET ?
            """,
            [*params, limit, offset],
        ).fetchall()
        items = [_project_card(db, row, user) for row in rows]

    return {"items": items, "total": total}


@router.post("/projects")
def share_project(
    req: ShareProjectRequest,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    title = req.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="项目标题不能为空")
    if len(title) > 120:
        raise HTTPException(status_code=400, detail="项目标题不能超过 120 位")
    if not _valid_category(req.category, req.subcategory):
        raise HTTPException(status_code=400, detail="分类选择不合法,请重新选择")

    phase_json, summary_json = _store_phase_data(req.phaseAnalysis)

    with _db() as db:
        cur = db.execute(
            """
            INSERT INTO community_projects
                (user_id, title, category, subcategory, procedure, surgeon, department, date,
                 duration, description, file_name, status, phase_data, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"], title, req.category, req.subcategory, req.procedure,
                req.surgeon, req.department, req.date, req.duration, req.description,
                req.fileName, req.status, phase_json, summary_json,
            ),
        )
        row = db.execute(
            """
            SELECT p.*, u.username
            FROM community_projects p JOIN users u ON u.id = p.user_id
            WHERE p.id = ?
            """,
            (cur.lastrowid,),
        ).fetchone()
        item = _project_card(db, row, user)

    return {"item": item}


@router.get("/projects/{project_id}")
def get_project(
    project_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    with _db() as db:
        row = db.execute(
            """
            SELECT p.*, u.username
            FROM community_projects p JOIN users u ON u.id = p.user_id
            WHERE p.id = ?
            """,
            (project_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="项目不存在或已删除")
        item = _project_card(db, row, user)
        try:
            phase_data = json.loads(row["phase_data"]) if row["phase_data"] else None
        except (ValueError, TypeError):
            phase_data = None
        item["phaseData"] = phase_data

    return {"item": item}


class QaRequest(BaseModel):
    question: str


@router.post("/projects/{project_id}/qa")
def project_qa(
    project_id: int,
    req: QaRequest,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """社区项目智能问答:基于该项目分享的分析数据回答,豆包驱动。"""
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="问题不能超过 500 字")

    with _db() as db:
        row = db.execute(
            """
            SELECT p.*, u.username
            FROM community_projects p JOIN users u ON u.id = p.user_id
            WHERE p.id = ?
            """,
            (project_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="项目不存在或已删除")
        try:
            phase_data = json.loads(row["phase_data"]) if row["phase_data"] else None
        except (TypeError, ValueError):
            phase_data = None

    context = {
        "标题": row["title"],
        "作者": row["username"],
        "分类": f'{row["category"] or ""} / {row["subcategory"] or ""}',
        "术式": row["procedure"] or "",
        "术者": row["surgeon"] or "",
        "所在科室": row["department"] or "",
        "手术日期": row["date"] or "",
        "视频时长": row["duration"] or "",
        "项目描述": row["description"] or "",
        "分享状态": row["status"] or "",
        "是否包含共享视频": "是" if row["video_file_name"] else "否",
        "视频文件名": row["video_file_name"] or "",
        "AI阶段分析": phase_data,
    }

    prompt = (
        "你是 SurgReview 手术视频分析平台的社区项目问答助手。"
        "请根据下面提供的社区共享项目数据回答用户问题,用中文回答,简洁专业。"
        "回答时区分'基于该项目分析'和'通用知识/推断'两部分来源。"
        "项目数据中不存在的信息不要编造;如果项目没有共享视频,不要声称看过视频画面。"
        "涉及医疗或手术建议时务必谨慎,并说明最终判断需要专业医师复核。\n\n"
        "项目数据:\n{}\n\n"
        "用户问题:\n{}"
    ).format(json.dumps(context, ensure_ascii=False, default=str), question)

    try:
        answer = call_doubao(prompt, None)
    except HTTPException as exc:
        raise exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="AI 服务暂时不可用,请稍后再试") from exc

    return {"answer": answer}


@router.put("/projects/{project_id}")
def update_project(
    project_id: int,
    req: ShareProjectRequest,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    title = req.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="项目标题不能为空")
    if not _valid_category(req.category, req.subcategory):
        raise HTTPException(status_code=400, detail="分类选择不合法,请重新选择")

    phase_json, summary_json = _store_phase_data(req.phaseAnalysis)

    with _db() as db:
        row = db.execute(
            "SELECT user_id FROM community_projects WHERE id = ?", (project_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="项目不存在或已删除")
        _check_owner(user, row["user_id"], "项目")

        db.execute(
            """
            UPDATE community_projects SET
                title = ?, category = ?, subcategory = ?, procedure = ?, surgeon = ?,
                department = ?, date = ?, duration = ?, description = ?, file_name = ?,
                status = ?, phase_data = ?, summary = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (
                title, req.category, req.subcategory, req.procedure, req.surgeon,
                req.department, req.date, req.duration, req.description, req.fileName,
                req.status, phase_json, summary_json, project_id,
            ),
        )
        updated = db.execute(
            """
            SELECT p.*, u.username
            FROM community_projects p JOIN users u ON u.id = p.user_id
            WHERE p.id = ?
            """,
            (project_id,),
        ).fetchone()
        item = _project_card(db, updated, user)

    return {"item": item}


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    with _db() as db:
        row = db.execute(
            "SELECT user_id, video_file_name FROM community_projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="项目不存在或已删除")
        _check_owner(user, row["user_id"], "项目")
        _purge_target(db, "project", project_id)
        db.execute("DELETE FROM community_projects WHERE id = ?", (project_id,))

    if row["video_file_name"]:
        _remove_video_file(project_id, row["video_file_name"])

    return {"message": "已删除"}


# ---------------------------------------------------------------- shared videos

@router.put("/projects/{project_id}/video")
async def upload_project_video(
    project_id: int,
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    with _db() as db:
        row = db.execute(
            "SELECT user_id FROM community_projects WHERE id = ?", (project_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="项目不存在或已删除")
        _check_owner(user, row["user_id"], "项目")

    file_name = file.filename or "video.mp4"
    target = _video_file(project_id, file_name)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    written_bytes = 0

    try:
        with target.open("wb") as fh:
            while True:
                chunk = await file.read(VIDEO_CHUNK_SIZE)
                if not chunk:
                    break
                fh.write(chunk)
                written_bytes += len(chunk)
                if written_bytes > VIDEO_MAX_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="视频体积超过 1GB 上限，请先压缩后再上传",
                    )
    except HTTPException:
        target.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    if written_bytes == 0:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="上传内容为空")

    with _db() as db:
        db.execute(
            "UPDATE community_projects SET video_file_name = ?, updated_at = datetime('now') WHERE id = ?",
            (file_name, project_id),
        )

    return {"message": "视频上传成功", "videoFileName": file_name}


@router.delete("/projects/{project_id}/video")
def delete_project_video(
    project_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    with _db() as db:
        row = db.execute(
            "SELECT user_id, video_file_name FROM community_projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="项目不存在或已删除")
        _check_owner(user, row["user_id"], "项目")

    if row["video_file_name"]:
        with _db() as db:
            db.execute(
                "UPDATE community_projects SET video_file_name = '', updated_at = datetime('now') WHERE id = ?",
                (project_id,),
            )
        _remove_video_file(project_id, row["video_file_name"])

    return {"message": "视频已删除"}


@router.get("/projects/{project_id}/video")
def stream_project_video(
    project_id: int,
    token: str = Query(default=None),
    download: bool = Query(default=False),
):
    """Stream a shared video to any logged-in user.

    <video> tags can't send an Authorization header, so the token travels as a
    query parameter. FileResponse handles HTTP Range requests natively, which
    keeps seeking and scrubbing working in the HTML5 player.

    download=1 switches to Content-Disposition: attachment so the browser
    saves the file instead of playing it.
    """
    with auth_db() as db:
        user = _get_user_by_token(db, token) if token else None
    if user is None:
        raise HTTPException(status_code=401, detail="登录凭证无效或已过期")

    with _db() as db:
        row = db.execute(
            "SELECT video_file_name FROM community_projects WHERE id = ?",
            (project_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="项目不存在或已删除")

    file_name = row["video_file_name"]
    if not file_name:
        raise HTTPException(status_code=404, detail="该项目未包含视频")

    path = _video_file(project_id, file_name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")

    return FileResponse(
        path,
        media_type="video/mp4",
        filename=file_name,
        content_disposition_type="attachment" if download else "inline",
    )


@router.get("/projects/{project_id}/export")
def export_project(
    project_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Download a shared project (any logged-in user).

    With a video: a ZIP bundle of project_info.json + the video file.
    Without: the JSON alone. Both served as attachments.
    """
    with _db() as db:
        row = db.execute(
            "SELECT * FROM community_projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="项目不存在或已删除")
        author = db.execute(
            "SELECT username FROM users WHERE id = ?", (row["user_id"],)
        ).fetchone()
        like_count = db.execute(
            "SELECT COUNT(*) FROM likes WHERE target_type='project' AND target_id=?",
            (project_id,),
        ).fetchone()[0]
        favorite_count = db.execute(
            "SELECT COUNT(*) FROM favorites WHERE target_type='project' AND target_id=?",
            (project_id,),
        ).fetchone()[0]
        comment_count = db.execute(
            "SELECT COUNT(*) FROM comments WHERE target_type='project' AND target_id=?",
            (project_id,),
        ).fetchone()[0]

    phase_data = None
    if row["phase_data"]:
        try:
            phase_data = json.loads(row["phase_data"])
        except (TypeError, ValueError):
            phase_data = None

    info = {
        "source": "SurgReview 开源社区",
        "exportedAt": datetime.now().isoformat(timespec="seconds"),
        "projectId": project_id,
        "title": row["title"],
        "category": row["category"] or "",
        "subcategory": row["subcategory"] or "",
        "author": author["username"] if author else "",
        "procedure": row["procedure"] or "",
        "surgeon": row["surgeon"] or "",
        "department": row["department"] or "",
        "date": row["date"] or "",
        "duration": row["duration"] or "",
        "description": row["description"] or "",
        "status": row["status"] or "",
        "hasVideo": bool(row["video_file_name"]),
        "videoFileName": row["video_file_name"] or "",
        "phaseAnalysis": phase_data,
        "stats": {
            "likeCount": like_count,
            "favoriteCount": favorite_count,
            "commentCount": comment_count,
        },
    }

    # 记录下载历史(同一项目重复下载刷新时间，显示在下载中心)。
    # 自己的项目本地本来就有，不算"从社区下载"，不记录。
    if row["user_id"] != user["id"]:
        with _db() as db:
            db.execute(
                "INSERT INTO downloads (user_id, project_id) VALUES (?, ?) "
                "ON CONFLICT(user_id, project_id) "
                "DO UPDATE SET created_at = datetime('now')",
                (user["id"], project_id),
            )

    video_path = (
        _video_file(project_id, row["video_file_name"])
        if row["video_file_name"]
        else None
    )
    if video_path is not None and video_path.exists():
        fd, tmp_path = tempfile.mkstemp(suffix=".zip")
        os.close(fd)
        try:
            with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_STORED) as zf:
                zf.writestr(
                    "project_info.json",
                    json.dumps(info, ensure_ascii=False, indent=2),
                )
                zf.write(video_path, arcname=row["video_file_name"])
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
        return FileResponse(
            tmp_path,
            media_type="application/zip",
            filename=f"project_{project_id}.zip",
            background=BackgroundTask(os.unlink, tmp_path),
        )

    # 无视频时直接返回 JSON 附件(不走 FileResponse content 参数,兼容旧版 starlette)
    return Response(
        content=json.dumps(info, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="project_{project_id}.json"'
        },
    )


@router.get("/me/downloads")
def my_downloads(
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """下载中心：当前用户下载过的项目列表(含视频大小)。"""
    with _db() as db:
        rows = db.execute(
            """
            SELECT d.project_id, d.created_at AS downloaded_at,
                   p.title, p.user_id AS author_id, u.username AS author,
                   p.video_file_name,
                   (SELECT COUNT(*) FROM likes l
                    WHERE l.target_type='project' AND l.target_id = d.project_id) AS like_count,
                   (SELECT COUNT(*) FROM favorites f
                    WHERE f.target_type='project' AND f.target_id = d.project_id) AS favorite_count
            FROM downloads d
            JOIN community_projects p ON p.id = d.project_id
            JOIN users u ON u.id = p.user_id
            WHERE d.user_id = ?
            ORDER BY d.created_at DESC
            """,
            (user["id"],),
        ).fetchall()
        items = []
        for r in rows:
            video_size = 0
            if r["video_file_name"]:
                path = _video_file(r["project_id"], r["video_file_name"])
                if path.exists():
                    video_size = path.stat().st_size
            items.append(
                {
                    "projectId": r["project_id"],
                    "title": r["title"],
                    "author": {"id": r["author_id"], "username": r["author"]},
                    "downloadedAt": r["downloaded_at"],
                    "hasVideo": bool(r["video_file_name"]),
                    "videoSize": video_size,
                    "likeCount": r["like_count"],
                    "favoriteCount": r["favorite_count"],
                }
            )
    return {"items": items}


@router.delete("/me/downloads/{project_id}")
def delete_download(
    project_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """删除一条下载记录(不影响已经下载到电脑的文件)。"""
    with _db() as db:
        db.execute(
            "DELETE FROM downloads WHERE user_id = ? AND project_id = ?",
            (user["id"], project_id),
        )
    return {"message": "下载记录已删除"}


# ---------------------------------------------------------------- feedback

FEEDBACK_TYPES = ("功能建议", "体验优化", "问题反馈", "其他")


class FeedbackRequest(BaseModel):
    type: str = "功能建议"
    content: str


def _feedback_card(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "type": row["type"],
        "content": row["content"],
        "status": row["status"],
        "reply": row["reply"] or "",
        "createdAt": row["created_at"],
    }


@router.post("/feedback")
def submit_feedback(
    req: FeedbackRequest,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    content = req.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="反馈内容不能为空")
    if len(content) > MAX_COMMENT_LENGTH:
        raise HTTPException(status_code=400, detail=f"反馈内容不能超过 {MAX_COMMENT_LENGTH} 字")
    if req.type not in FEEDBACK_TYPES:
        raise HTTPException(status_code=400, detail="反馈类型不合法")

    with _db() as db:
        cur = db.execute(
            "INSERT INTO feedback (user_id, type, content) VALUES (?, ?, ?)",
            (user["id"], req.type, content),
        )
        row = db.execute(
            "SELECT * FROM feedback WHERE id = ?", (cur.lastrowid,)
        ).fetchone()

    return {"item": _feedback_card(row)}


@router.get("/feedback")
def list_my_feedback(
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """当前用户的反馈记录(按提交时间倒序)。"""
    with _db() as db:
        rows = db.execute(
            "SELECT * FROM feedback WHERE user_id = ? ORDER BY id DESC",
            (user["id"],),
        ).fetchall()

    return {"items": [_feedback_card(row) for row in rows]}


@router.delete("/feedback/{feedback_id}")
def delete_feedback(
    feedback_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    with _db() as db:
        row = db.execute(
            "SELECT user_id FROM feedback WHERE id = ?", (feedback_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="反馈不存在或已删除")
        _check_owner(user, row["user_id"], "反馈")
        db.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))

    return {"message": "已删除"}


# ---------------------------------------------------------------- posts

class PostRequest(BaseModel):
    title: str
    content: str


@router.get("/posts")
def list_posts(
    q: str = "",
    limit: int = PAGE_SIZE,
    offset: int = 0,
    mine: bool = False,
    author_id: Optional[int] = None,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    conditions: list = []
    params: list = []
    keyword = (q or "").strip()
    if keyword:
        like = f"%{keyword}%"
        conditions.append("(po.title LIKE ? OR po.content LIKE ? OR u.username LIKE ?)")
        params += [like, like, like]
    if mine:
        conditions.append("po.user_id = ?")
        params.append(user["id"])
    if author_id is not None:
        conditions.append("po.user_id = ?")
        params.append(author_id)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    with _db() as db:
        total = db.execute(
            f"SELECT COUNT(*) FROM posts po JOIN users u ON u.id = po.user_id {where}",
            params,
        ).fetchone()[0]
        rows = db.execute(
            f"""
            SELECT po.*, u.username
            FROM posts po JOIN users u ON u.id = po.user_id
            {where}
            ORDER BY po.created_at DESC
            LIMIT ? OFFSET ?
            """,
            [*params, limit, offset],
        ).fetchall()
        items = [_post_card(db, row, user) for row in rows]

    return {"items": items, "total": total}


@router.post("/posts")
def create_post(
    req: PostRequest,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    title = req.title.strip()
    content = req.content.strip()
    if not title:
        raise HTTPException(status_code=400, detail="帖子标题不能为空")
    if len(title) > 120:
        raise HTTPException(status_code=400, detail="帖子标题不能超过 120 位")
    if not content:
        raise HTTPException(status_code=400, detail="帖子内容不能为空")
    if len(content) > 20000:
        raise HTTPException(status_code=400, detail="帖子内容不能超过 20000 字")

    with _db() as db:
        cur = db.execute(
            "INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)",
            (user["id"], title, content),
        )
        row = db.execute(
            "SELECT po.*, u.username FROM posts po JOIN users u ON u.id = po.user_id WHERE po.id = ?",
            (cur.lastrowid,),
        ).fetchone()
        item = _post_card(db, row, user)

    return {"item": item}


@router.get("/posts/{post_id}")
def get_post(
    post_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    with _db() as db:
        row = db.execute(
            "SELECT po.*, u.username FROM posts po JOIN users u ON u.id = po.user_id WHERE po.id = ?",
            (post_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="帖子不存在或已删除")
        item = _post_card(db, row, user)
        item["content"] = row["content"]

    return {"item": item}


@router.put("/posts/{post_id}")
def update_post(
    post_id: int,
    req: PostRequest,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    title = req.title.strip()
    content = req.content.strip()
    if not title:
        raise HTTPException(status_code=400, detail="帖子标题不能为空")
    if not content:
        raise HTTPException(status_code=400, detail="帖子内容不能为空")

    with _db() as db:
        row = db.execute(
            "SELECT user_id FROM posts WHERE id = ?", (post_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="帖子不存在或已删除")
        _check_owner(user, row["user_id"], "帖子")

        db.execute(
            "UPDATE posts SET title = ?, content = ?, updated_at = datetime('now') WHERE id = ?",
            (title, content, post_id),
        )
        updated = db.execute(
            "SELECT po.*, u.username FROM posts po JOIN users u ON u.id = po.user_id WHERE po.id = ?",
            (post_id,),
        ).fetchone()
        item = _post_card(db, updated, user)
        item["content"] = updated["content"]

    return {"item": item}


@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    with _db() as db:
        row = db.execute(
            "SELECT user_id FROM posts WHERE id = ?", (post_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="帖子不存在或已删除")
        _check_owner(user, row["user_id"], "帖子")
        _purge_target(db, "post", post_id)
        db.execute("DELETE FROM posts WHERE id = ?", (post_id,))

    return {"message": "已删除"}


# ---------------------------------------------------------------- comments

class CommentRequest(BaseModel):
    target_type: str
    target_id: int
    content: str
    parent_id: Optional[int] = None


@router.get("/comments")
def list_comments(
    user: Dict[str, Any] = Depends(get_current_user),
    target_type: str = "",
    target_id: int = 0,
    mine: bool = False,
) -> Dict[str, Any]:
    with _db() as db:
        if mine:
            rows = db.execute(
                """
                SELECT c.*, u.username,
                       COALESCE(p.title, po.title) AS target_title
                FROM comments c
                JOIN users u ON u.id = c.user_id
                LEFT JOIN community_projects p
                    ON p.id = c.target_id AND c.target_type = 'project'
                LEFT JOIN posts po
                    ON po.id = c.target_id AND c.target_type = 'post'
                WHERE c.user_id = ?
                ORDER BY c.created_at DESC
                """,
                (user["id"],),
            ).fetchall()
            items = []
            for r in rows:
                reply_count = db.execute(
                    "SELECT COUNT(*) FROM comments WHERE parent_id = ?", (r["id"],)
                ).fetchone()[0]
                items.append(
                    {
                        "id": r["id"],
                        "targetType": r["target_type"],
                        "targetId": r["target_id"],
                        "targetTitle": r["target_title"] or "",
                        "content": r["content"],
                        "createdAt": r["created_at"],
                        "isMine": True,
                        "replyCount": reply_count,
                    }
                )
            return {"items": items}

        _check_target_type(target_type)
        _require_target(db, target_type, target_id)
        rows = db.execute(
            """
            SELECT c.*, u.username
            FROM comments c JOIN users u ON u.id = c.user_id
            WHERE c.target_type = ? AND c.target_id = ?
            ORDER BY c.created_at ASC
            """,
            (target_type, target_id),
        ).fetchall()
        flat = [
            {
                "id": r["id"],
                "parentId": r["parent_id"],
                "author": {"id": r["user_id"], "username": r["username"]},
                "content": r["content"],
                "createdAt": r["created_at"],
                "isMine": r["user_id"] == user["id"],
                "replies": [],
            }
            for r in rows
        ]
        # 组树:回复挂到其父评论下,顶级评论保持创建顺序
        by_id = {item["id"]: item for item in flat}
        items = []
        for item in flat:
            parent = by_id.get(item["parentId"])
            if parent is not None:
                parent["replies"].append(item)
            else:
                items.append(item)

    return {"items": items}


@router.post("/comments")
def create_comment(
    req: CommentRequest,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    _check_target_type(req.target_type)
    content = req.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="评论内容不能为空")
    if len(content) > MAX_COMMENT_LENGTH:
        raise HTTPException(
            status_code=400, detail=f"评论不能超过 {MAX_COMMENT_LENGTH} 字"
        )

    with _db() as db:
        _require_target(db, req.target_type, req.target_id)
        if req.parent_id is not None:
            parent = db.execute(
                "SELECT target_type, target_id, parent_id FROM comments WHERE id = ?",
                (req.parent_id,),
            ).fetchone()
            if parent is None:
                raise HTTPException(status_code=404, detail="要回复的评论不存在或已删除")
            if (
                parent["target_type"] != req.target_type
                or parent["target_id"] != req.target_id
            ):
                raise HTTPException(
                    status_code=400, detail="要回复的评论不属于当前内容"
                )

        cur = db.execute(
            """
            INSERT INTO comments (user_id, target_type, target_id, content, parent_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user["id"], req.target_type, req.target_id, content, req.parent_id),
        )
        row = db.execute(
            """
            SELECT c.*, u.username
            FROM comments c JOIN users u ON u.id = c.user_id
            WHERE c.id = ?
            """,
            (cur.lastrowid,),
        ).fetchone()
        item = {
            "id": row["id"],
            "parentId": row["parent_id"],
            "author": {"id": row["user_id"], "username": row["username"]},
            "content": row["content"],
            "createdAt": row["created_at"],
            "isMine": True,
            "replies": [],
        }

    return {"item": item}


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    with _db() as db:
        row = db.execute(
            "SELECT user_id, target_type, target_id FROM comments WHERE id = ?",
            (comment_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="评论不存在或已删除")
        if row["user_id"] != user["id"]:
            # 评论作者之外,内容(项目/帖子)发布者也可以删除其下的评论
            if row["target_type"] == "project":
                owner = db.execute(
                    "SELECT user_id FROM community_projects WHERE id = ?",
                    (row["target_id"],),
                ).fetchone()
            else:
                owner = db.execute(
                    "SELECT user_id FROM posts WHERE id = ?", (row["target_id"],)
                ).fetchone()
            if owner is None or owner["user_id"] != user["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="只能删除自己的评论或自己发布内容下的评论",
                )
        db.execute("DELETE FROM comments WHERE id = ?", (comment_id,))

    return {"message": "已删除"}


# ---------------------------------------------------------------- likes / favorites

def _set_like(
    user: Dict[str, Any], target_type: str, target_id: int, liked: bool
) -> Dict[str, Any]:
    _check_target_type(target_type)
    with _db() as db:
        _require_target(db, target_type, target_id)
        if liked:
            db.execute(
                "INSERT OR IGNORE INTO likes (user_id, target_type, target_id) VALUES (?, ?, ?)",
                (user["id"], target_type, target_id),
            )
        else:
            db.execute(
                "DELETE FROM likes WHERE user_id = ? AND target_type = ? AND target_id = ?",
                (user["id"], target_type, target_id),
            )
        count = db.execute(
            "SELECT COUNT(*) FROM likes WHERE target_type = ? AND target_id = ?",
            (target_type, target_id),
        ).fetchone()[0]
    return {"liked": liked, "count": count}


def _set_favorite(
    user: Dict[str, Any], target_type: str, target_id: int, favorited: bool
) -> Dict[str, Any]:
    _check_target_type(target_type)
    with _db() as db:
        _require_target(db, target_type, target_id)
        if favorited:
            db.execute(
                "INSERT OR IGNORE INTO favorites (user_id, target_type, target_id) VALUES (?, ?, ?)",
                (user["id"], target_type, target_id),
            )
        else:
            db.execute(
                "DELETE FROM favorites WHERE user_id = ? AND target_type = ? AND target_id = ?",
                (user["id"], target_type, target_id),
            )
        count = db.execute(
            "SELECT COUNT(*) FROM favorites WHERE target_type = ? AND target_id = ?",
            (target_type, target_id),
        ).fetchone()[0]
    return {"favorited": favorited, "count": count}


@router.post("/projects/{project_id}/like")
def like_project(
    project_id: int, user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    return _set_like(user, "project", project_id, True)


@router.delete("/projects/{project_id}/like")
def unlike_project(
    project_id: int, user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    return _set_like(user, "project", project_id, False)


@router.post("/posts/{post_id}/like")
def like_post(
    post_id: int, user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    return _set_like(user, "post", post_id, True)


@router.delete("/posts/{post_id}/like")
def unlike_post(
    post_id: int, user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    return _set_like(user, "post", post_id, False)


@router.post("/projects/{project_id}/favorite")
def favorite_project(
    project_id: int, user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    return _set_favorite(user, "project", project_id, True)


@router.delete("/projects/{project_id}/favorite")
def unfavorite_project(
    project_id: int, user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    return _set_favorite(user, "project", project_id, False)


@router.post("/posts/{post_id}/favorite")
def favorite_post(
    post_id: int, user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    return _set_favorite(user, "post", post_id, True)


@router.delete("/posts/{post_id}/favorite")
def unfavorite_post(
    post_id: int, user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    return _set_favorite(user, "post", post_id, False)


# ---------------------------------------------------------------- follows / feed

@router.post("/users/{user_id}/follow")
def follow_user(
    user_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="不能关注自己")
    with _db() as db:
        target = db.execute(
            "SELECT id FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if target is None:
            raise HTTPException(status_code=404, detail="用户不存在")
        db.execute(
            "INSERT OR IGNORE INTO follows (follower_id, followee_id) VALUES (?, ?)",
            (user["id"], user_id),
        )
        count = db.execute(
            "SELECT COUNT(*) FROM follows WHERE followee_id = ?", (user_id,)
        ).fetchone()[0]
    return {"following": True, "followingCount": count}


@router.delete("/users/{user_id}/follow")
def unfollow_user(
    user_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    with _db() as db:
        db.execute(
            "DELETE FROM follows WHERE follower_id = ? AND followee_id = ?",
            (user["id"], user_id),
        )
        count = db.execute(
            "SELECT COUNT(*) FROM follows WHERE followee_id = ?", (user_id,)
        ).fetchone()[0]
    return {"following": False, "followingCount": count}


@router.get("/users/{user_id}/profile")
def user_profile(
    user_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    with _db() as db:
        target = db.execute(
            "SELECT id, username, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if target is None:
            raise HTTPException(status_code=404, detail="用户不存在")

        project_count = db.execute(
            "SELECT COUNT(*) FROM community_projects WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
        post_count = db.execute(
            "SELECT COUNT(*) FROM posts WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
        follower_count = db.execute(
            "SELECT COUNT(*) FROM follows WHERE followee_id = ?", (user_id,)
        ).fetchone()[0]
        following_count = db.execute(
            "SELECT COUNT(*) FROM follows WHERE follower_id = ?", (user_id,)
        ).fetchone()[0]
        is_following = db.execute(
            "SELECT 1 FROM follows WHERE follower_id = ? AND followee_id = ?",
            (user["id"], user_id),
        ).fetchone() is not None
        is_self = user["id"] == user_id

        projects = db.execute(
            """
            SELECT p.*, u.username
            FROM community_projects p JOIN users u ON u.id = p.user_id
            WHERE p.user_id = ?
            ORDER BY p.created_at DESC LIMIT 3
            """,
            (user_id,),
        ).fetchall()
        posts = db.execute(
            """
            SELECT po.*, u.username
            FROM posts po JOIN users u ON u.id = po.user_id
            WHERE po.user_id = ?
            ORDER BY po.created_at DESC LIMIT 3
            """,
            (user_id,),
        ).fetchall()
        recent_projects = [_project_card(db, r, user) for r in projects]
        recent_posts = [_post_card(db, r, user) for r in posts]

    return {
        "user": dict(target),
        "stats": {
            "projectCount": project_count,
            "postCount": post_count,
            "followerCount": follower_count,
            "followingCount": following_count,
        },
        "isFollowing": is_following,
        "isSelf": is_self,
        "recentProjects": recent_projects,
        "recentPosts": recent_posts,
    }


@router.get("/feed")
def get_feed(
    limit: int = PAGE_SIZE,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    limit = max(1, min(limit, 100))
    with _db() as db:
        rows = db.execute(
            """
            SELECT 'project' AS item_type, p.id AS id, p.title AS title,
                   p.created_at AS created_at, p.user_id AS user_id, u.username AS username
            FROM community_projects p JOIN users u ON u.id = p.user_id
            WHERE p.user_id IN (SELECT followee_id FROM follows WHERE follower_id = ?)
            UNION ALL
            SELECT 'post' AS item_type, po.id AS id, po.title AS title,
                   po.created_at AS created_at, po.user_id AS user_id, u.username AS username
            FROM posts po JOIN users u ON u.id = po.user_id
            WHERE po.user_id IN (SELECT followee_id FROM follows WHERE follower_id = ?)
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user["id"], user["id"], limit),
        ).fetchall()
        items = [
            {
                "itemType": r["item_type"],
                "id": r["id"],
                "title": r["title"],
                "author": {"id": r["user_id"], "username": r["username"]},
                "createdAt": r["created_at"],
            }
            for r in rows
        ]

    return {"items": items}


# ---------------------------------------------------------------- my likes / favorites

def _my_engagement(user: Dict[str, Any], table: str) -> Dict[str, Any]:
    """当前用户的收藏或点赞列表(项目 + 帖子,含目标标题/作者)。"""
    with _db() as db:
        rows = db.execute(
            f"""
            SELECT l.target_type, l.target_id, l.created_at,
                   COALESCE(p.title, po.title) AS target_title,
                   COALESCE(p.user_id, po.user_id) AS target_author_id,
                   COALESCE(pu.username, pou.username) AS target_author
            FROM {table} l
            LEFT JOIN community_projects p
                ON p.id = l.target_id AND l.target_type = 'project'
            LEFT JOIN posts po
                ON po.id = l.target_id AND l.target_type = 'post'
            LEFT JOIN users pu ON pu.id = p.user_id
            LEFT JOIN users pou ON pou.id = po.user_id
            WHERE l.user_id = ? AND (p.id IS NOT NULL OR po.id IS NOT NULL)
            ORDER BY l.created_at DESC
            """,
            (user["id"],),
        ).fetchall()
        items = [
            {
                "targetType": r["target_type"],
                "targetId": r["target_id"],
                "targetTitle": r["target_title"] or "",
                "targetAuthorId": r["target_author_id"],
                "targetAuthor": r["target_author"] or "",
                "createdAt": r["created_at"],
                "favorited": table == "favorites",
                "liked": table == "likes",
            }
            for r in rows
        ]
    return {"items": items}


@router.get("/me/favorites")
def my_favorites(
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    return _my_engagement(user, "favorites")


@router.get("/me/likes")
def my_likes(
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    return _my_engagement(user, "likes")


@router.get("/me/following")
def my_following(
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """我关注的博主列表(带统计与最近动态)。"""
    with _db() as db:
        rows = db.execute(
            """
            SELECT u.id, u.username, u.created_at,
                   (SELECT COUNT(*) FROM community_projects p WHERE p.user_id = u.id) AS project_count,
                   (SELECT COUNT(*) FROM posts po WHERE po.user_id = u.id) AS post_count,
                   (SELECT COUNT(*) FROM follows f WHERE f.followee_id = u.id) AS follower_count,
                   (SELECT p.title FROM community_projects p
                    WHERE p.user_id = u.id ORDER BY p.created_at DESC LIMIT 1) AS latest_project,
                   (SELECT po.title FROM posts po
                    WHERE po.user_id = u.id ORDER BY po.created_at DESC LIMIT 1) AS latest_post,
                   (SELECT MAX(x) FROM (
                       SELECT p.created_at AS x FROM community_projects p WHERE p.user_id = u.id
                       UNION ALL
                       SELECT po.created_at AS x FROM posts po WHERE po.user_id = u.id
                   )) AS latest_at
            FROM follows f
            JOIN users u ON u.id = f.followee_id
            WHERE f.follower_id = ?
            ORDER BY latest_at DESC NULLS LAST
            """,
            (user["id"],),
        ).fetchall()
        items = [
            {
                "id": r["id"],
                "username": r["username"],
                "createdAt": r["created_at"],
                "projectCount": r["project_count"],
                "postCount": r["post_count"],
                "followerCount": r["follower_count"],
                "latestProject": r["latest_project"] or "",
                "latestPost": r["latest_post"] or "",
                "latestAt": r["latest_at"] or "",
            }
            for r in rows
        ]
    return {"items": items}
