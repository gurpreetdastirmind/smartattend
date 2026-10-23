from pydantic import BaseModel
from typing import List, Optional


class ClassCreate(BaseModel):
    name: str


class StudentCreate(BaseModel):
    class_id: int
    roll_no: str
    full_name: str
    consent: bool


class RosterRow(BaseModel):
    student_id: Optional[int] = None
    roll_no: str = ""
    full_name: str = ""
    status: str = "UNMARKED"


class SaveAttendance(BaseModel):
    session_id: int
    rows: List[RosterRow]