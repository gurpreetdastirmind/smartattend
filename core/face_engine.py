import cv2 as cv
import numpy as np
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

DETECTOR = cv.FaceDetectorYN.create(
    str(MODELS_DIR / "face_detection_yunet_2023mar.onnx"),
    "",
    (320, 320),
    score_threshold=0.85,
    nms_threshold=0.3,
    top_k=5000,
)

RECOGNIZER = cv.FaceRecognizerSF.create(
    str(MODELS_DIR / "face_recognition_sface_2021dec.onnx"),
    "",
)


def detect_embeddings(bgr: np.ndarray) -> list[dict]:
    """Return [{face, embedding}]. face = [x,y,w,h,landmarks...]"""
    h, w = bgr.shape[:2]
    DETECTOR.setInputSize((w, h))
    _, faces = DETECTOR.detect(bgr)
    results = []
    if faces is None:
        return results
    for face in faces:
        aligned = RECOGNIZER.alignCrop(bgr, face)
        emb = RECOGNIZER.feature(aligned).astype(np.float32).ravel()
        norm = max(float(np.linalg.norm(emb)), 1e-12)
        emb = emb / norm
        results.append({"face": face, "embedding": emb})
    return results