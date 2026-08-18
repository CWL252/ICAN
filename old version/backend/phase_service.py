import math
import os
from pathlib import Path

import albumentations as A
import cv2
import torch
from albumentations.pytorch import ToTensorV2

from phase_model import PhaseModel


PHASE_DEFINITIONS = {
    0: {
        "key": "preparation",
        "label": "术前准备",
        "en_label": "Preparation",
        "description": "建立手术视野并完成器械与解剖区域准备。",
    },
    1: {
        "key": "calot_triangle_dissection",
        "label": "胆囊三角解剖",
        "en_label": "CalotTriangleDissection",
        "description": "暴露 Calot 三角区域，识别胆囊管与胆囊动脉。",
    },
    2: {
        "key": "clipping_cutting",
        "label": "夹闭切断",
        "en_label": "ClippingCutting",
        "description": "对关键管道进行夹闭并完成切断。",
    },
    3: {
        "key": "gallbladder_dissection",
        "label": "胆囊剥离",
        "en_label": "GallbladderDissection",
        "description": "沿胆囊床继续剥离，完成胆囊主体游离。",
    },
    4: {
        "key": "gallbladder_packaging",
        "label": "胆囊装袋",
        "en_label": "GallbladderPackaging",
        "description": "将切除后的胆囊置入取物袋准备移出。",
    },
    5: {
        "key": "cleaning_coagulation",
        "label": "清理止血",
        "en_label": "CleaningCoagulation",
        "description": "对创面进行清理、冲洗和止血凝固处理。",
    },
    6: {
        "key": "gallbladder_retraction",
        "label": "胆囊牵引",
        "en_label": "GallbladderRetraction",
        "description": "通过牵引调整暴露视野，为后续操作创造条件。",
    },
}


class PhaseInferenceService:
    def __init__(self):
        backend_dir = Path(__file__).resolve().parent
        local_weights_dir = backend_dir / "pretrained_weights"
        configured_root = Path(os.getenv("SURGPHASE_ROOT", r"D:\project\SurgPhase"))

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_root = backend_dir if local_weights_dir.exists() else configured_root
        self.weights_dir = local_weights_dir if local_weights_dir.exists() else configured_root / "pretrained_weights"
        self.model = PhaseModel(device=self.device, weights_dir=self.weights_dir)
        self.transform = A.Compose(
            [
                A.SmallestMaxSize(max_size=256),
                A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
                ToTensorV2(),
            ]
        )

    def health(self):
        return {
            "model_loaded": True,
            "device": str(self.device),
            "weights_dir": str(self.weights_dir),
            "phase_count": len(PHASE_DEFINITIONS),
        }

    def analyze_video(self, video_path, sample_seconds=2.0, confidence_threshold=0.65, progress_callback=None):
        self._report_progress(progress_callback, "preprocessing", "数据预处理", "正在读取视频信息并计算采样间隔。", 20)
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError("无法打开待分析视频文件。")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = frame_count / fps if frame_count and fps else 0
        sample_interval = max(1, int(round(fps * max(sample_seconds, 0.25))))

        sample_indices = list(range(0, max(frame_count, 1), sample_interval))
        predictions = []

        self.model.reset()

        self._report_progress(progress_callback, "inference", "模型推理", "正在对采样帧执行阶段识别推理。", 35)
        total_samples = max(len(sample_indices), 1)
        with torch.inference_mode():
            for sample_index, frame_index in enumerate(sample_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                success, frame = cap.read()
                if not success:
                    continue

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                tensor = self.transform(image=frame_rgb)["image"].unsqueeze(0).unsqueeze(0).to(self.device)
                output = self.model.net(tensor)
                logits = output[-1]
                probabilities = torch.softmax(logits, dim=2)
                confidence, pred = probabilities.max(dim=2)
                phase_id = int(pred.item())

                predictions.append(
                    {
                        "frameIndex": frame_index,
                        "seconds": round(frame_index / fps, 2),
                        "phaseId": phase_id,
                        "phaseKey": PHASE_DEFINITIONS[phase_id]["key"],
                        "phaseLabel": PHASE_DEFINITIONS[phase_id]["label"],
                        "confidence": round(float(confidence.item()), 4),
                    }
                )
                if sample_index == len(sample_indices) - 1 or sample_index % 5 == 0:
                    progress = 35 + int(((sample_index + 1) / total_samples) * 50)
                    self._report_progress(
                        progress_callback,
                        "inference",
                        "模型推理",
                        f"正在分析采样帧 {sample_index + 1}/{total_samples}。",
                        min(progress, 85),
                    )

        cap.release()

        self._report_progress(progress_callback, "postprocessing", "整理结果", "正在合并阶段片段并生成时间线。", 90)
        segments = self._merge_predictions(predictions, duration)
        steps = [segment for segment in segments if segment["confidence"] >= confidence_threshold]
        if not steps and segments:
            steps = [max(segments, key=lambda item: item["confidence"])]
        phase_distribution = self._build_distribution(segments, duration)

        return {
            "meta": {
                "fps": round(fps, 2),
                "frameCount": frame_count,
                "durationSeconds": round(duration, 2),
                "sampleSeconds": sample_seconds,
                "sampleCount": len(predictions),
                "device": str(self.device),
                "confidenceThreshold": confidence_threshold,
            },
            "steps": steps,
            "segments": segments,
            "predictions": predictions,
            "distribution": phase_distribution,
        }

    @staticmethod
    def _report_progress(progress_callback, stage, label, message, progress):
        if progress_callback:
            progress_callback(stage, label, message, progress)

    def _merge_predictions(self, predictions, duration):
        if not predictions:
            return []

        steps = []
        current = {
            "phaseId": predictions[0]["phaseId"],
            "phaseKey": predictions[0]["phaseKey"],
            "phaseLabel": predictions[0]["phaseLabel"],
            "startSeconds": predictions[0]["seconds"],
            "endSeconds": predictions[0]["seconds"],
            "confidences": [predictions[0]["confidence"]],
        }

        for item in predictions[1:]:
            if item["phaseId"] == current["phaseId"]:
                current["endSeconds"] = item["seconds"]
                current["confidences"].append(item["confidence"])
                continue

            steps.append(self._format_step(current, len(steps) + 1, duration))
            current = {
                "phaseId": item["phaseId"],
                "phaseKey": item["phaseKey"],
                "phaseLabel": item["phaseLabel"],
                "startSeconds": item["seconds"],
                "endSeconds": item["seconds"],
                "confidences": [item["confidence"]],
            }

        steps.append(self._format_step(current, len(steps) + 1, duration))
        return steps

    def _format_step(self, segment, index, duration):
        phase_meta = PHASE_DEFINITIONS[segment["phaseId"]]
        avg_confidence = sum(segment["confidences"]) / max(len(segment["confidences"]), 1)
        start_seconds = segment["startSeconds"]
        end_seconds = segment["endSeconds"]
        if math.isclose(start_seconds, end_seconds) and duration > end_seconds:
            end_seconds = min(duration, end_seconds + 2)

        return {
            "id": f"step-{index}",
            "index": index,
            "phaseId": segment["phaseId"],
            "phaseKey": segment["phaseKey"],
            "title": phase_meta["label"],
            "time": f"{format_seconds(start_seconds)} - {format_seconds(end_seconds)}",
            "startSeconds": round(start_seconds, 2),
            "endSeconds": round(end_seconds, 2),
            "seconds": round(start_seconds, 2),
            "confidence": round(avg_confidence, 4),
            "level": "高置信度" if avg_confidence >= 0.65 else "建议复核",
            "description": phase_meta["description"],
        }

    def _build_distribution(self, steps, duration):
        distribution = []
        for phase_id, phase_meta in PHASE_DEFINITIONS.items():
            total = 0.0
            for step in steps:
                if step["phaseId"] == phase_id:
                    total += max(0, step["endSeconds"] - step["startSeconds"])

            distribution.append(
                {
                    "phaseId": phase_id,
                    "phaseKey": phase_meta["key"],
                    "phaseLabel": phase_meta["label"],
                    "seconds": round(total, 2),
                    "ratio": round((total / duration), 4) if duration else 0,
                }
            )
        return distribution


def format_seconds(value):
    if not value or value < 0:
        return "00:00"
    minutes = int(value // 60)
    seconds = int(value % 60)
    return f"{minutes:02d}:{seconds:02d}"
