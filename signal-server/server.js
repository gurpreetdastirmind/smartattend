const http = require("http");
const express = require("express");
const { Server } = require("socket.io");

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: { origin: ["https://smartattend-frontend-nu.vercel.app/", "http://localhost:5173"] },
  maxHttpBufferSize: 1e7,
});

const rooms = new Map();

app.get("/", (_req, res) => res.send("SmartAttend signaling up"));

io.on("connection", (socket) => {
  console.log("client connected:", socket.id);

  socket.on("create-room", (roomId, ack) => {
    rooms.set(roomId, { laptopId: socket.id });
    socket.join(roomId);
    console.log("room created:", roomId);
    ack?.({ ok: true });
  });

  socket.on("join-room", (roomId, ack) => {
    if (!rooms.has(roomId)) return ack?.({ ok: false, reason: "no_room" });
    socket.join(roomId);
    socket.to(roomId).emit("phone-joined");
    console.log("phone joined:", roomId);
    ack?.({ ok: true });
  });

  socket.on("photo", ({ roomId, dataUrl }) => {
    socket.to(roomId).emit("photo", { dataUrl });
  });

  socket.on("disconnect", () => {
    for (const [rid, v] of rooms) {
      if (v.laptopId === socket.id) {
        rooms.delete(rid);
        io.to(rid).emit("room-closed");
      }
    }
  });
});

server.listen(4000, () => console.log("Signaling :4000"));