import axios from "axios";

// Si tu backend corre en 127.0.0.1:8000, dejalo asi
export const API = axios.create({ baseURL: "http://127.0.0.1:8000/api" });

export const listAsteroids = () => API.get("/asteroids");
export const getAsteroidDetail = (id: string) => API.get(`/asteroids/${id}`);
export const simulateImpact = (payload: any) => API.post("/simulate", payload);
export const getAsteroidOrbit = (id: string) => API.get(`/asteroids/${id}/orbit`);

