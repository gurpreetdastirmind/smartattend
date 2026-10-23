import { useEffect, useMemo, useRef, useState } from "react";
import { io } from "socket.io-client";
import { QRCodeCanvas } from "qrcode.react";
import { API, SIGNAL_URL } from "../api.js";
import RosterTable from "../components/RosterTable.jsx";

export default function LaptopView() {
  const [roomId] = useState(
    () => `room-${Math.random().toString(36).slice(2, 8)}`
  );
  const [phoneJoined, setPhoneJoined] = useState(false);
  const [photoDataUrl, setPhotoDataUrl] = useState(null);
  const [classes, setClasses] = useState([]);
  const [classId, setClassId] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [annotated, setAnnotated] = useState(null);
  const [faces, setFaces] = useState([]);
  const [rows, setRows] = useState([]);
  const socketRef = useRef(null);

  useEffect(() => {
    const socket = io(SIGNAL_URL);
    socket.emit("create-room", roomId);
    socket.on("phone-joined", () => setPhoneJoined(true));
    socket.on("photo", ({ dataUrl }) => setPhotoDataUrl(dataUrl));
    socketRef.current = socket;
    return () => socket.disconnect();
  }, [roomId]);

  useEffect(() => {
    API.get("/classes").then((r) => setClasses(r.data)).catch(console.error);
  }, []);

  const phoneUrl = useMemo(
    () => `${window.location.origin}/phone/${roomId}`,
    [roomId]
  );

  async function runRecognition() {
    if (!photoDataUrl || !classId || !sessionId) {
      alert("Pick class, enter session ID, and wait for a photo.");
      return;
    }
    const blob = await (await fetch(photoDataUrl)).blob();
    const fd = new FormData();
    fd.append("class_id", classId);
    fd.append("session_id", sessionId);
    fd.append("file", blob, "capture.jpg");
    const res = await API.post("/recognize", fd);
    setAnnotated("data:image/jpeg;base64," + res.data.annotated_image_b64);
    setFaces(res.data.faces);
    setRows(
      res.data.faces.map((f) => ({
        student_id: f.student_id,
        roll_no: f.student_id ? String(f.student_id) : "-",
        full_name: f.name ?? "UNKNOWN",
        status:
          f.status === "SUGGEST_PRESENT"
            ? "PRESENT"
            : "UNMARKED",
      }))
    );
  }

  async function save() {
    await API.post("/attendance/save", {
      session_id: Number(sessionId),
      rows,
    });
    alert("Saved!");
  }

  function exportXlsx() {
    window.open(`${API.defaults.baseURL}/export/${sessionId}`, "_blank");
  }

  return (
    <div style={page}>
      <h1>SmartAttend AI — Control Center</h1>

      <section style={panel}>
        <h3>1) Scan QR with phone</h3>
        <QRCodeCanvas value={phoneUrl} size={180} />
        <p>
          Room: <code>{roomId}</code> —{" "}
          {phoneJoined ? "📱 Connected" : "⌛ Waiting…"}
        </p>
        <small>Phone URL: {phoneUrl}</small>
      </section>

      <section style={panel}>
        <h3>2) Class & session</h3>
        <select value={classId} onChange={(e) => setClassId(e.target.value)}>
          <option value="">-- class --</option>
          {classes.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>{" "}
        <input
          placeholder="Session ID (e.g. 1)"
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          style={{ marginLeft: 8 }}
        />
      </section>

      <section style={panel}>
        <h3>3) Captured photo</h3>
        {photoDataUrl ? (
          <>
            <img
              src={photoDataUrl}
              alt="capture"
              style={{ maxWidth: 400, borderRadius: 8 }}
            />
            <br />
            <button onClick={runRecognition} style={btn}>
              Run recognition
            </button>
          </>
        ) : (
          <p>Waiting for phone…</p>
        )}
      </section>

      {annotated && (
        <section style={panel}>
          <h3>4) Annotated result</h3>
          <img
            src={annotated}
            alt="annotated"
            style={{ maxWidth: 600, borderRadius: 8 }}
          />
          <ul>
            {faces.map((s, i) => (
              <li key={i}>
                #{i + 1} — {s.name ?? "UNKNOWN"} ({s.status},{" "}
                {s.score.toFixed(3)})
              </li>
            ))}
          </ul>
        </section>
      )}

      {rows.length > 0 && (
        <section style={panel}>
          <h3>5) Review & approve</h3>
          <RosterTable rows={rows} setRows={setRows} />
          <button onClick={save} style={btn}>
            Save
          </button>{" "}
          <button onClick={exportXlsx} style={btn}>
            Export .xlsx
          </button>
        </section>
      )}
    </div>
  );
}

const page = { padding: 24, fontFamily: "system-ui", maxWidth: 900, margin: "0 auto" };
const panel = {
  background: "#f7f7f7",
  padding: 16,
  margin: "16px 0",
  borderRadius: 8,
};
const btn = {
  padding: "10px 16px",
  background: "#2563eb",
  color: "#fff",
  border: 0,
  borderRadius: 6,
  cursor: "pointer",
  marginTop: 8,
};