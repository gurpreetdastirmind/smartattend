import base64
import cv2 as cv
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from core import database, attendance
from core.face_engine import detect_embeddings
from core.matcher import rank_candidates
from backend.schemas import ClassCreate, StudentCreate, SaveAttendance

app = FastAPI(title="SmartAttend AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

database.init()

@app.get("/")
def root():
    return {"status": "ok", "app": "SmartAttend AI"}

@app.post("/classes")
def create_class(p: ClassCreate):
    return database.create_class(p.name)

@app.get("/classes")
def list_classes():
    return database.list_classes()

@app.post("/students")
def create_student(p: StudentCreate):
    if not p.consent:
        raise HTTPException(400, "Consent required")
    return database.create_student(p.class_id, p.roll_no, p.full_name)

@app.get("/students/{class_id}")
def list_students(class_id: int):
    return database.list_students(class_id)

@app.post("/students/{student_id}/enroll")
async def enroll_face(student_id: int, file: UploadFile = File(...)):
    raw = await file.read()
    bgr = _decode(raw)
    faces = detect_embeddings(bgr)
    if len(faces) != 1:
        raise HTTPException(400, f"Expected exactly 1 face, found {len(faces)}")
    database.add_embedding(student_id, faces[0]["embedding"])
    return {"ok": True}

@app.post("/sessions")
def create_session(class_id: int = Form(...), subject: str = Form("Demo")):
    sid = database.ensure_session(class_id, -1, subject)
    return {"session_id": sid}

@app.post("/recognize")
async def recognize(
    class_id: int = Form(...),
    session_id: int = Form(...),
    file: UploadFile = File(...),
):
    raw = await file.read()
    bgr = _decode(raw)
    detections = detect_embeddings(bgr)
    enrolled = database.embeddings_for_class(class_id)
    ranked = rank_candidates(detections, enrolled)

    annotated = bgr.copy()
    for i, r in enumerate(ranked):
        face = detections[r["face_index"]]["face"]
        x, y, w, h = face[:4].astype(int)
        cv.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv.putText(annotated, str(i + 1), (x, y - 8), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    ok, buf = cv.imencode(".jpg", annotated)
    if not ok:
        raise HTTPException(500, "Image encoding failed")
    b64 = base64.b64encode(buf).decode("ascii")

    return {"session_id": session_id, "annotated_image_b64": b64, "faces": ranked}

@app.post("/attendance/save")
def save_attendance(p: SaveAttendance):
    attendance.save_approved(p.session_id, [r.dict() for r in p.rows])
    return {"ok": True}

@app.get("/export/{session_id}")
def export_xlsx(session_id: int):
    buf = attendance.export_excel(session_id)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=attendance_{session_id}.xlsx"},
    )

def _decode(raw: bytes) -> np.ndarray:
    arr = np.frombuffer(raw, np.uint8)
    img = cv.imdecode(arr, cv.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "Invalid image")
    return img