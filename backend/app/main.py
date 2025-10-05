from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import NASA_API_KEY
from app.routers import asteroids, simulate

app = FastAPI(title="DEIMOS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(asteroids.router, prefix="/api/asteroids", tags=["asteroids"])
app.include_router(simulate.router,  prefix="/api/simulate",  tags=["simulate"])

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/key")
def key():
    return {"NASA_API_KEY": NASA_API_KEY}
