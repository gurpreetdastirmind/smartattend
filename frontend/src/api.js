import axios from "axios";

export const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

export const SIGNAL_URL =
  import.meta.env.VITE_SIGNAL_URL || "http://localhost:4000";