import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { io } from "socket.io-client";
import Webcam from "react-webcam";
import { SIGNAL_URL } from "../api.js";

export default function PhoneView() {
  const { roomId } = useParams();
  const socketRef = useRef(null);
  const camRef = useRef(null);
  const [joined, setJoined] = useState(false);

  useEffect(() => {
    const socket = io(SIGNAL_URL);
    socket.emit("join-room", roomId, (resp) => {
      if (resp?.ok) setJoined(true);
      else alert("Room not found — refresh QR on laptop");
    });
    socketRef.current = socket;
    return () => socket.disconnect();
  }, [roomId]);

  function capture() {
    const dataUrl = camRef.current?.getScreenshot();
    if (!dataUrl) return;
    socketRef.current.emit("photo", { roomId, dataUrl });
    alert("Sent to laptop ✅");
  }

  return (
    <div style={{ padding: 12, fontFamily: "system-ui" }}>
      <h2>SmartAttend — Camera</h2>
      <p>{joined ? "Connected ✅" : "Connecting…"}</p>
      <Webcam
        ref={camRef}
        audio={false}
        screenshotFormat="image/jpeg"
        videoConstraints={{ facingMode: "environment", width: 1280 }}
        style={{ width: "100%", borderRadius: 12 }}
      />
      <button
        onClick={capture}
        disabled={!joined}
        style={{
          width: "100%",
          padding: 16,
          marginTop: 16,
          fontSize: 18,
          background: joined ? "#16a34a" : "#999",
          color: "#fff",
          border: 0,
          borderRadius: 8,
        }}
      >
        📸 Capture & Send
      </button>
    </div>
  );
}