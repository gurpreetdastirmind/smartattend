import io
import pandas as pd
from core.database import SessionLocal, Student, Attendance

def save_approved(session_id: int, rows: list[dict]):
    from core.database import save_attendance_rows
    save_attendance_rows(session_id, rows)

def export_excel(session_id: int) -> io.BytesIO:
    with SessionLocal() as db:
        results = db.query(Student.roll_no, Student.full_name, Attendance.status)\
                    .join(Attendance, Attendance.student_id == Student.id)\
                    .filter(Attendance.session_id == session_id)\
                    .order_by(Student.roll_no).all()

    data = [{"Roll No": r.roll_no, "Student Name": r.full_name, "Status": r.status} for r in results]
    df = pd.DataFrame(data, columns=["Roll No", "Student Name", "Status"])
    df["Reviewed By"] = "Teacher"

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Attendance")
    buf.seek(0)
    return buf