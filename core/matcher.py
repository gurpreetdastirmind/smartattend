import numpy as np

# Tunable — adjust on a small validation set (spec §10)
THRESHOLD = 0.363
MARGIN = 0.05


def rank_candidates(detections, enrolled):
    """
    detections: list of {"face", "embedding"}
    enrolled:   list of {"student_id", "name", "roll_no", "embedding"}
    Returns:    list of {face_index, student_id, name, status, score}
    """
    if not enrolled:
        return [
            {"face_index": i, "student_id": None, "name": None,
             "status": "UNKNOWN", "score": 0.0}
            for i in range(len(detections))
        ]

    results = []
    used_students = set()

    for i, det in enumerate(detections):
        det_emb = det["embedding"]

        # Best score per student (max over their 2-3 samples)
        per_student = {}
        for enr in enrolled:
            sim = float(np.dot(det_emb, enr["embedding"]))
            sid = enr["student_id"]
            if sim > per_student.get(sid, {}).get("score", -1):
                per_student[sid] = {"score": sim, "name": enr["name"]}

        ranked = sorted(per_student.items(), key=lambda kv: kv[1]["score"], reverse=True)
        top_sid, top = ranked[0]
        second_score = ranked[1][1]["score"] if len(ranked) > 1 else -1

        # Decision tree (spec §10)
        if top["score"] < THRESHOLD:
            status, sid, name = "UNKNOWN", None, None
        elif (top["score"] - second_score) < MARGIN:
            status, sid, name = "NEEDS_REVIEW", top_sid, top["name"]
        elif top_sid in used_students:
            status, sid, name = "NEEDS_REVIEW", top_sid, top["name"]
        else:
            status, sid, name = "SUGGEST_PRESENT", top_sid, top["name"]
            used_students.add(top_sid)

        results.append({
            "face_index": i,
            "student_id": sid,
            "name": name,
            "status": status,
            "score": round(top["score"], 4),
        })
    return results