import { BrowserRouter, Routes, Route } from "react-router-dom";
import LaptopView from "./pages/LaptopView.jsx";
import PhoneView from "./pages/PhoneView.jsx";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LaptopView />} />
        <Route path="/phone/:roomId" element={<PhoneView />} />
      </Routes>
    </BrowserRouter>
  );
}