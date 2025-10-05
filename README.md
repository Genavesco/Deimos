# DEIMOS - Asteroid Impact Simulator

DEIMOS is a full-stack tool built for the 2025 NASA Space Apps Challenge that lets teams explore potentially hazardous asteroid (PHA) data from NASA JPL, simulate impact scenarios, and visualise local consequences on an interactive map and 3D viewer.

## Features
- Fetches latest PHA catalogue data and orbital elements from NASA JPL Small-Body Database (SBDB)
- Summarises impact risk, Palermo/Torino scales, and derived physical properties
- Site-aware impact simulations with crater, shock, thermal, tsunami, and casualty estimates
- Interactive map for selecting impact coordinates plus 3D builder for asteroid geometry
- Caching and offline fallbacks so rehearsed demos continue to work during judging

## Project Structure
```
backend/   FastAPI application exposing the REST API and simulation models
frontend/  React + Vite single-page app that consumes the API
docs/      Submission templates, asset checklists, and other supporting material
```

## Getting Started
These instructions assume Windows 11 + PowerShell, but the commands translate to macOS/Linux shells.

### 1. Clone or copy the project
```
# Replace <your-gh-account> with your GitHub username once the repo exists
git clone https://github.com/<your-gh-account>/deimos.git
cd deimos
```

### 2. Backend API
```
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
copy .env.example .env   # or `cp` on macOS/Linux
```
Edit `.env` and set `NASA_API_KEY`. You can use `DEMO_KEY` for light testing, but request a personal key from https://api.nasa.gov for production reliability.

Run the API:
```
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
The OpenAPI docs become available at http://127.0.0.1:8000/docs.

### 3. Frontend
Open a new terminal:
```
cd frontend
npm install
npm run dev -- --host
```
The dev server listens on http://127.0.0.1:5173. Ensure the backend stays on `127.0.0.1:8000` (the default Axios base URL is defined in `frontend/src/lib/api.ts`).

### 4. Optional quality checks
- Backend: `python -m pip install pytest` then `python -m pytest`
- Frontend: `npm run lint` and `npm run build`

## Deployment Checklist
- [ ] Backend deployed (or ran locally) and reachable via HTTPS for production demos
- [ ] Frontend built with `npm run build` and hosted (Netlify, Vercel, GitHub Pages, etc.)
- [ ] `.env` populated with a working `NASA_API_KEY`
- [ ] Cache directory `backend/app/data/sbdb` populated (run `GET /api/asteroids` once before demo if network is limited)
- [ ] Demo video or slide deck recorded and uploaded (see `docs/demo-outline.md`)

## Data Sources
NASA data (required for eligibility):
- **JPL Small-Body Database (SBDB)** via `https://ssd-api.jpl.nasa.gov/sbdb_query.api` and `sbdb.api`
- **JPL SBDB orbit elements** for trajectory visualisation

Additional open datasets and services:
- **OpenTopoData ETOPO1** (NOAA/NGDC) for elevation, slope, and roughness estimates
- **OpenStreetMap Nominatim** reverse geocoding for landform categorisation and ISO country codes
- **World Bank EN.POP.DNST indicator** for country-level population density

Document external assets (images, textures, fonts) in `docs/resources.md` before submission.

## NASA Submission Materials
The hackathon judges evaluate the content you enter on the Space Apps project page. We maintain a living draft of each field in [`docs/nasa_submission.md`](docs/nasa_submission.md). Update that file before you paste the final copy into the official form.

### Demo requirements
NASA requires either a 30-second video (with English subtitles) or a 7-slide deck. Use [`docs/demo-outline.md`](docs/demo-outline.md) as a script/storyboard template and store the rendered asset in a public link (YouTube, Google Drive, etc.).

## Publishing on GitHub
1. Sign in to GitHub and create a **public** repository named `deimos` (or another name of your choice).
2. Initialise Git locally if you have not already:
   ```
   git init
   git branch -M main
   git remote add origin https://github.com/<your-gh-account>/deimos.git
   ```
3. Commit and push:
   ```
   git add .
   git commit -m "Initial open submission"
   git push -u origin main
   ```
4. Create a release tag (optional but helpful for judges):
   ```
   git tag -a v1.0.0 -m "Space Apps 2025 submission"
   git push origin v1.0.0
   ```
5. Enable GitHub Pages or your preferred hosting for the built frontend bundle if you want a live demo.

## Submission Checklist (Space Apps 2025)
- [ ] Complete every required field on the Space Apps project page (use the template in `docs/nasa_submission.md`)
- [ ] Provide a public link to the demo video or slide deck
- [ ] Provide a public link to the GitHub repository (and live site if available)
- [ ] Confirm AI usage disclosure (section in `docs/nasa_submission.md`)
- [ ] Review Terms, Privacy Policy, and originality confirmation before clicking **Submit for Judging**

## Contact & Support
If you run into issues while following this guide, capture terminal output or screenshots and add them to the repository issues so the team can triage quickly during hackathon crunch time.
