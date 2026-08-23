from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from job_manager import PhaseJobManager
from phase_service import PhaseInferenceService
from sam_service import SamModelUnavailableError, sam_service
from auth import get_current_user, router as auth_router
from community import router as community_router
from llm import call_doubao


app = FastAPI(title="SurgInsight Phase Analysis API", version="0.1.0")

app.include_router(auth_router)
app.include_router(community_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5180",
        "http://localhost:5180",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

job_manager = PhaseJobManager(service_factory=PhaseInferenceService)


class ChatRequest(BaseModel):
    question: str
    context: Optional[Dict[str, Any]] = None


class SegmentPoint(BaseModel):
    x: float
    y: float
    label: int  # 1 = 正样本点, 0 = 负样本点


class SegmentRequest(BaseModel):
    image: str  # base64 编码的当前帧（JPEG/PNG）
    points: List[SegmentPoint]
    frame_width: Optional[float] = None
    frame_height: Optional[float] = None


class SegmentAnnotation(BaseModel):
    phaseKey: str
    phaseLabel: str = ""
    startSeconds: float
    endSeconds: float
    edited: bool = False
    source: str = "ai"


class PhaseAnnotationsRequest(BaseModel):
    segments: List[SegmentAnnotation]


@app.get("/health")
def health():
    result = {
        "status": "ok",
        "model_loaded": False,
        "message": "Phase inference model will be loaded when the first analysis job runs.",
    }
    if job_manager.is_service_loaded():
        result = job_manager.service.health()
    result["sam_model_loaded"] = sam_service.is_loaded()
    return result


@app.post("/api/segment")
async def segment(
    request: SegmentRequest,
    current_user: Any = Depends(get_current_user),
):
    if not request.points:
        raise HTTPException(status_code=400, detail="请至少提供一个样本点。")

    try:
        payload = await run_in_threadpool(
            sam_service.segment,
            request.image,
            [p.model_dump() for p in request.points],
            request.frame_width,
            request.frame_height,
        )
    except SamModelUnavailableError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="分割推理失败：{}".format(exc)) from exc

    return {"status": "ok", **payload}


@app.post("/api/phase/jobs")
async def create_phase_job(
    file: UploadFile = File(...),
    sample_seconds: float = 2.0,
    current_user: Any = Depends(get_current_user),
):
    try:
        return await job_manager.create_job_from_upload(file, sample_seconds=sample_seconds)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/phase/jobs/{job_id}")
async def get_phase_job(
    job_id: str,
    current_user: Any = Depends(get_current_user),
):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Phase analysis job was not found.")
    return job


@app.put("/api/phase/jobs/{job_id}/annotations")
async def save_phase_annotations(
    job_id: str,
    request: PhaseAnnotationsRequest,
    current_user: Any = Depends(get_current_user),
):
    annotations = [segment.model_dump() for segment in request.segments]
    job = job_manager.save_annotations(job_id, annotations)
    if not job:
        raise HTTPException(status_code=404, detail="Phase analysis job was not found.")
    return job


@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    current_user: Any = Depends(get_current_user),
):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        answer = await run_in_threadpool(call_doubao, question, request.context)
        return {"answer": answer}
    except HTTPException:
        raise
    except Exception as exc:
        error_text = str(exc)
        if "connection" in error_text.lower():
            detail = (
                "Doubao API connection failed. Check whether this Python environment can access "
                "https://ark.cn-beijing.volces.com and verify proxy/SSL certificate settings. "
                "Original error: {}".format(error_text)
            )
        else:
            detail = "Doubao API call failed: {}".format(error_text)
        raise HTTPException(status_code=500, detail=detail) from exc
