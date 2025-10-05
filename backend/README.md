# DEIMOS Backend

FastAPI service that powers the DEIMOS asteroid impact simulator.

## Key Endpoints
- `GET /api/health` -- health check for uptime monitors
- `GET /api/asteroids` -- cached list of potentially hazardous asteroids (PHA) ordered by impact probability
- `GET /api/asteroids/{spkid}` -- detail view with derived physics metrics
- `GET /api/asteroids/{spkid}/orbit` -- orbital elements for visualisations
- `POST /api/simulate` -- run a site-specific impact simulation

## Running Locally
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Set `NASA_API_KEY` in `.env` (default `DEMO_KEY` works for light use but has rate limits). The service caches SBDB payloads in `app/data/sbdb` for faster demos.

## Tests
Install pytest if it is not already available in the virtualenv:
```
python -m pip install pytest
python -m pytest
```

## Code Style
- Python 3.11+
- Ruff or black are recommended for linting/formatting (optional)
- Keep new datasets and services documented in `docs/resources.md`
