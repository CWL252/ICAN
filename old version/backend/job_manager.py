import json
import threading
import uuid
from datetime import datetime
from pathlib import Path


UPLOAD_CHUNK_SIZE = 1024 * 1024


class PhaseJobManager:
    def __init__(self, service=None, service_factory=None, runtime_dir=None):
        self.service = service
        self.service_factory = service_factory
        self.runtime_dir = Path(runtime_dir or Path(__file__).resolve().parent / "runtime")
        self.jobs_dir = self.runtime_dir / "jobs"
        self.uploads_dir = self.runtime_dir / "uploads"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._service_lock = threading.Lock()

    def create_job(self, file_bytes, file_name, sample_seconds=2.0):
        job_id = f"phase-job-{uuid.uuid4().hex}"
        suffix = Path(file_name or "video.mp4").suffix or ".mp4"
        video_path = self.uploads_dir / f"{job_id}{suffix}"
        video_path.write_bytes(file_bytes)

        if not file_bytes:
            video_path.unlink(missing_ok=True)
            raise ValueError("上传内容为空。")

        return self._queue_job(job_id, video_path, file_name, sample_seconds)

    async def create_job_from_upload(self, upload_file, sample_seconds=2.0):
        file_name = upload_file.filename or "video.mp4"
        job_id = f"phase-job-{uuid.uuid4().hex}"
        suffix = Path(file_name).suffix or ".mp4"
        video_path = self.uploads_dir / f"{job_id}{suffix}"
        written_bytes = 0

        try:
            with video_path.open("wb") as file:
                while True:
                    chunk = await upload_file.read(UPLOAD_CHUNK_SIZE)
                    if not chunk:
                        break
                    file.write(chunk)
                    written_bytes += len(chunk)
        finally:
            await upload_file.close()

        if written_bytes == 0:
            video_path.unlink(missing_ok=True)
            raise ValueError("上传内容为空。")

        return self._queue_job(job_id, video_path, file_name, sample_seconds)

    def _queue_job(self, job_id, video_path, file_name, sample_seconds):
        job = {
            "jobId": job_id,
            "status": "queued",
            "stage": "queued",
            "stageLabel": "排队中",
            "message": "关键步骤分析任务已创建，等待后台处理。",
            "progress": 0,
            "fileName": file_name or "video.mp4",
            "sampleSeconds": sample_seconds,
            "createdAt": self._now(),
            "updatedAt": self._now(),
            "result": None,
            "error": None,
            "videoPath": str(video_path),
        }
        self._save_job(job)

        worker = threading.Thread(target=self._run_job, args=(job_id,), daemon=True)
        worker.start()
        return self._public_job(job)

    def get_job(self, job_id):
        job = self._load_job(job_id)
        if not job:
            return None
        return self._public_job(job)

    def _run_job(self, job_id):
        job = self._load_job(job_id)
        if not job:
            return

        try:
            self._update_job_progress(job, "running", "loading_model", "加载模型", "正在加载阶段识别模型和权重。", 10)
            service = self._get_service()

            result = service.analyze_video(
                job["videoPath"],
                sample_seconds=job.get("sampleSeconds", 2.0),
                progress_callback=lambda stage, label, message, progress: self._update_job_progress(
                    job,
                    "running",
                    stage,
                    label,
                    message,
                    progress,
                ),
            )
            job["status"] = "completed"
            job["stage"] = "completed"
            job["stageLabel"] = "分析完成"
            job["message"] = "关键步骤分析完成。"
            job["progress"] = 100
            job["result"] = result
            job["updatedAt"] = self._now()
            self._save_job(job)
        except Exception as exc:  # noqa: BLE001
            job["status"] = "failed"
            job["stage"] = "failed"
            job["stageLabel"] = "分析失败"
            job["message"] = str(exc)
            job["progress"] = job.get("progress", 0)
            job["error"] = str(exc)
            job["updatedAt"] = self._now()
            self._save_job(job)

    def _update_job_progress(self, job, status, stage, stage_label, message, progress):
        job["status"] = status
        job["stage"] = stage
        job["stageLabel"] = stage_label
        job["message"] = message
        job["progress"] = progress
        job["updatedAt"] = self._now()
        self._save_job(job)

    def _get_service(self):
        if self.service:
            return self.service
        if not self.service_factory:
            raise RuntimeError("Phase inference service is not configured.")

        with self._service_lock:
            if not self.service:
                self.service = self.service_factory()
        return self.service

    def is_service_loaded(self):
        return self.service is not None

    def _job_file(self, job_id):
        return self.jobs_dir / f"{job_id}.json"

    def _load_job(self, job_id):
        job_file = self._job_file(job_id)
        if not job_file.exists():
            return None
        with job_file.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _save_job(self, job):
        with self._lock:
            job_file = self._job_file(job["jobId"])
            with job_file.open("w", encoding="utf-8") as file:
                json.dump(job, file, ensure_ascii=False, indent=2)

    def _public_job(self, job):
        return {
            "jobId": job["jobId"],
            "status": job["status"],
            "stage": job.get("stage"),
            "stageLabel": job.get("stageLabel"),
            "message": job.get("message"),
            "progress": job.get("progress", 0),
            "fileName": job.get("fileName"),
            "sampleSeconds": job.get("sampleSeconds"),
            "createdAt": job.get("createdAt"),
            "updatedAt": job.get("updatedAt"),
            "result": job.get("result"),
            "error": job.get("error"),
        }

    @staticmethod
    def _now():
        return datetime.now().isoformat()
