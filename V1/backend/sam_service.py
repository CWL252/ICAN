import base64
import threading
import time
from pathlib import Path

import cv2
import numpy as np
import torch

from mobile_sam import sam_model_registry, SamPredictor

CHECKPOINT_PATH = Path(__file__).resolve().parent / "pretrained_weights" / "mobile_sam.pt"


class SamModelUnavailableError(RuntimeError):
    pass


class SamService:
    def __init__(self):
        self._lock = threading.Lock()
        self._model = None
        self._predictor = None
        self._device = None

    def ensure_loaded(self):
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            if not CHECKPOINT_PATH.exists():
                raise SamModelUnavailableError(
                    "MobileSAM 权重文件缺失：pretrained_weights/mobile_sam.pt"
                )
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model = sam_model_registry["vit_t"](checkpoint=str(CHECKPOINT_PATH)).to(self._device)
            model.eval()
            self._model = model
            self._predictor = SamPredictor(model)

    def is_loaded(self):
        return self._model is not None

    def health(self):
        return {
            "model_loaded": self.is_loaded(),
            "device": str(self._device) if self._device else "not-loaded",
            "weights": str(CHECKPOINT_PATH),
        }

    def segment(self, image_b64, points, frame_width, frame_height):
        started = time.perf_counter()
        self.ensure_loaded()

        # Accept either raw base64 or a data: URL fragment
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]
        raw = base64.b64decode(image_b64)
        image_bgr = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if image_bgr is None:
            raise ValueError("无法解码上传的图像。")
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        h, w = image_rgb.shape[:2]

        # Build point arrays, clamp into frame bounds
        coords, labels = [], []
        for pt in points:
            x = max(0, min(w - 1, int(round(float(pt["x"])))))
            y = max(0, min(h - 1, int(round(float(pt["y"])))))
            coords.append([x, y])
            labels.append(1 if int(pt["label"]) == 1 else 0)
        if not coords or 1 not in labels:
            raise ValueError("请至少提供一个正样本点。")

        with torch.inference_mode():
            self._predictor.set_image(image_rgb)
            masks, scores, _ = self._predictor.predict(
                point_coords=np.array(coords, dtype=np.float32),
                point_labels=np.array(labels, dtype=np.int32),
                multimask_output=True,
            )
            best = int(np.argmax(scores))
            mask = masks[best].astype(np.uint8) * 255

        polygon = self._extract_polygon(mask)
        if polygon is None:
            ys, xs = np.where(mask > 0)
            if len(xs) == 0:
                raise ValueError("模型未能生成掩码，请调整样本点后重试。")
            polygon = [
                [int(xs.min()), int(ys.min())],
                [int(xs.max()), int(ys.min())],
                [int(xs.max()), int(ys.max())],
                [int(xs.min()), int(ys.max())],
            ]
            ok, buf = cv2.imencode(".png", mask)
            mask_png = base64.b64encode(buf.tobytes()).decode("ascii") if ok else None
        else:
            mask_png = None

        return {
            "polygon": polygon,
            "mask_png": mask_png,
            "device": str(self._device),
            "elapsed_ms": round((time.perf_counter() - started) * 1000),
        }

    @staticmethod
    def _extract_polygon(mask):
        closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(contour) < 50:
            return None
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        points = [[int(p[0][0]), int(p[0][1])] for p in approx]
        return points if len(points) >= 3 else None


sam_service = SamService()
