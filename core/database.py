import os
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, LargeBinary, Float, UniqueConstraint, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Setup Connection (Neon if DATABASE_URL is set, else local SQLite)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Fix for SQLAlchemy requiring 'postgresql://' instead of 'postgres://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL)
else:
    # Fallback to local SQLite for development
    engine = create_engine("sqlite:///./data/smartattend.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Define Models (Tables)
class Class(Base):
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(String, nullable=False)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    roll_no = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    consent_at = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint('class_id', 'roll_no', name='_class_roll_uc'),)

class Embedding(Base):
    __tablename__ = "embeddings"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    feature_blob = Column(LargeBinary, nullable=False)
    model_version = Column(String, nullable=False)
    created_at = Column(String, nullable=False)

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    session_date = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    created_at = Column(String, nullable=False)
    approved_at = Column(String, nullable=True)

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    status = Column(String, nullable=False)
    match_score = Column(Float, nullable=True)
    source = Column(String, nullable=True)
    reviewed_at = Column(String, nullable=True)
    __table_args__ = (UniqueConstraint('session_id', 'student_id', name='_session_student_uc'),)

# 3. Initialize DB
def init():
    Base.metadata.create_all(bind=engine)

# 4. CRUD Functions (Using SQLAlchemy)
def create_class(name: str):
    with SessionLocal() as db:
        new_class = Class(name=name, created_at=datetime.utcnow().isoformat())
        db.add(new_class)
        db.commit()
        db.refresh(new_class)
        return {"id": new_class.id, "name": new_class.name}

def list_classes():
    with SessionLocal() as db:
        classes = db.query(Class).all()
        return [{"id": c.id, "name": c.name, "created_at": c.created_at} for c in classes]

def create_student(class_id: int, roll_no: str, full_name: str):
    with SessionLocal() as db:
        new_student = Student(
            class_id=class_id, roll_no=roll_no, full_name=full_name,
            consent_at=datetime.utcnow().isoformat()
        )
        db.add(new_student)
        db.commit()
        db.refresh(new_student)
        return {"id": new_student.id, "class_id": class_id, "roll_no": roll_no, "full_name": full_name}

def list_students(class_id: int):
    with SessionLocal() as db:
        students = db.query(Student).filter(Student.class_id == class_id).all()
        return [{"id": s.id, "class_id": s.class_id, "roll_no": s.roll_no, "full_name": s.full_name} for s in students]

def add_embedding(student_id: int, emb: np.ndarray, model_version="sface_2021dec"):
    with SessionLocal() as db:
        new_emb = Embedding(
            student_id=student_id,
            feature_blob=emb.astype(np.float32).tobytes(),
            model_version=model_version,
            created_at=datetime.utcnow().isoformat()
        )
        db.add(new_emb)
        db.commit()

def embeddings_for_class(class_id: int):
    with SessionLocal() as db:
        results = db.query(Embedding.student_id, Student.full_name, Student.roll_no, Embedding.feature_blob)\
                    .join(Student, Student.id == Embedding.student_id)\
                    .filter(Student.class_id == class_id).all()
    return [
        {
            "student_id": r.student_id,
            "name": r.full_name,
            "roll_no": r.roll_no,
            "embedding": np.frombuffer(r.feature_blob, dtype=np.float32),
        } for r in results
    ]

def ensure_session(class_id: int, session_id: int, subject="Demo"):
    with SessionLocal() as db:
        if session_id == -1:
            new_session = Session(
                class_id=class_id, session_date=datetime.utcnow().date().isoformat(),
                subject=subject, created_at=datetime.utcnow().isoformat()
            )
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            return new_session.id
        
        existing = db.query(Session).filter(Session.id == session_id).first()
        return existing.id if existing else None

def save_attendance_rows(session_id: int, rows: list[dict]):
    with SessionLocal() as db:
        for r in rows:
            if not r.get("student_id"):
                continue
            
            existing = db.query(Attendance).filter_by(session_id=session_id, student_id=r["student_id"]).first()
            if existing:
                existing.status = r["status"]
                existing.reviewed_at = datetime.utcnow().isoformat()
            else:
                new_att = Attendance(
                    session_id=session_id, student_id=r["student_id"], status=r["status"],
                    source="teacher", reviewed_at=datetime.utcnow().isoformat()
                )
                db.add(new_att)
        
        # Update session approved time
        sess = db.query(Session).filter(Session.id == session_id).first()
        if sess:
            sess.approved_at = datetime.utcnow().isoformat()
            
        db.commit()