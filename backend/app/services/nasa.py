import httpx
from app.config import NASA_API_KEY

BASE_NEOWS = "https://api.nasa.gov/neo/rest/v1"
SBDB = "https://ssd-api.jpl.nasa.gov/sbdb.api"

async def search_asteroids_by_name(q: str):
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(SBDB, params={"des": q})
        if resp.status_code != 200:
            return None
        return resp.json()

async def popular_asteroids_seed():
    return [
        {"name": "99942 Apophis"},
        {"name": "101955 Bennu"},
        {"name": "25143 Itokawa"},
        {"name": "162173 Ryugu"},
        {"name": "433 Eros"},
    ]
