"""豆包(火山引擎 Ark)大模型调用封装:分析页 AI 助手与社区项目智能问答共用。"""
import os
from typing import Any, Dict, List, Optional

from fastapi import HTTPException


# Doubao Ark settings.
# Fill these values for local development. Environment variables take priority.
DOUBAO_API_KEY = "ark-58470ec4-0bd0-4763-8a90-08f5c77056bf-b32d4"
DOUBAO_MODEL = "doubao-seed-2-0-mini-260428"
DOUBAO_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

ark_client = None


def get_ark_client():
    global ark_client
    if ark_client is not None:
        return ark_client

    api_key = os.getenv("ARK_API_KEY") or DOUBAO_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ARK API key is not configured. Fill DOUBAO_API_KEY in backend/llm.py.",
        )

    try:
        from volcenginesdkarkruntime import Ark
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="Ark SDK is not installed. Run: pip install volcengine-python-sdk[ark]",
        ) from exc

    ark_client = Ark(
        base_url=os.getenv("ARK_BASE_URL") or DOUBAO_BASE_URL,
        api_key=api_key,
    )
    return ark_client


def extract_ark_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return str(output_text)

    if hasattr(response, "model_dump"):
        response = response.model_dump()
    elif not isinstance(response, (dict, list, str)):
        response = getattr(response, "__dict__", response)

    if isinstance(response, str):
        return response

    if isinstance(response, dict):
        choices = response.get("choices")
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content")
            if content:
                return str(content)

    text_parts: List[str] = []

    def walk(value: Any):
        if isinstance(value, dict):
            if value.get("type") in {"output_text", "text"} and value.get("text"):
                text_parts.append(str(value["text"]))
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(response)
    return "\n".join(text_parts).strip() or str(response)


def build_chat_prompt(question: str, context: Optional[Dict[str, Any]]) -> str:
    return (
        "You are the intelligent Q&A assistant in the SurgReview surgical video analysis system. "
        "Answer in Chinese. Prioritize the provided current video analysis context, but you may also use general surgical, "
        "medical, and perioperative knowledge when the context is insufficient. Clearly separate evidence from the current "
        "video context and general knowledge or inference. Use labels such as '基于当前视频分析' and '通用知识/推断'. "
        "Do not claim that something was observed in this video unless it is present in the provided context. "
        "For medical or surgical advice, be cautious and state that final judgment requires qualified clinician review. "
        "Be concise and professional.\n\n"
        "Current analysis context:\n{}\n\n"
        "User question:\n{}".format(context or {}, question)
    )


def call_doubao(question: str, context: Optional[Dict[str, Any]]) -> str:
    client = get_ark_client()
    model = os.getenv("ARK_MODEL") or DOUBAO_MODEL
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": build_chat_prompt(question, context),
            }
        ],
    )
    return extract_ark_text(response)
