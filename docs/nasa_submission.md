# NASA Space Apps Submission Draft

Update each section before pasting into the official project page. Replace bracketed placeholders (`<>`) with your team-specific details.

## Project Name
DEIMOS - Asteroid Impact Simulator

## High-Level Project Summary
DEIMOS is a planetary-defense decision support app that pulls the latest potentially hazardous asteroid catalogue from NASA JPL and simulates impact scenarios anywhere on Earth. It translates orbital and physical parameters into plain-language effects (crater size, shock wave, thermal radius, tsunami, population exposure) so emergency planners can understand risk quickly and explore mitigation strategies.

## Link to Project Demo
[<https://youtu.be/your-demo-url>](https://youtu.be/QxxIGrBYcx4)

Create a 30-second video with English subtitles **or** a seven-slide deck (see `docs/demo-outline.md`). Host it on a public link with no login required.

## Link to Final Project
<https://github.com/genavesco/deimos>

Provide the public GitHub repository URL (and optionally link to a live deployment if you host the frontend).

## Detailed Project Description
- **What it does:**
  - Lists potential impactors from the NASA SBDB catalogue, sorted by impact probability.
  - Offers a guided simulator where teams pick an asteroid, tune physical parameters, and drop it on an interactive map.
  - Computes crater diameter, shock and thermal footprints, tsunami height (for ocean strikes), casualty estimates, and global survival probability.
  - Visualises the blast zones on a Leaflet map and includes a Three.js asteroid builder for storytelling.
- **How it works:**
  - FastAPI backend fetches SBDB data, caches it locally, and runs physics models derived from Purdue Impact equations.
  - Geo-intelligence comes from OpenTopoData and OpenStreetMap to tailor gravity, slope, and surface density.
  - World Bank population density data plus heuristic fallbacks feed exposure estimates; all results are returned as JSON.
  - Vite/React frontend consumes the API, orchestrates the simulation workflow, and renders WebGL/Leaflet components.
- **Benefits / impact:**
  - Gives local authorities and educators an intuitive view of planetary defense scenarios.
  - Speeds up comparative analysis between mitigation options by running multiple what-if simulations within minutes.
  - Creates an accessible outreach experience that demystifies NASA's open data for the public.
- **Roadmap:**
  - Add impact mitigation playbooks (deflection mission timelines, evacuation modelling).
  - Support offline-first demos by bundling a curated SBDB snapshot.
  - Layer in socio-economic datasets to tailor casualty and cost estimates for specific regions.
- **Stack:** Python 3.11, FastAPI, httpx, pydantic, React 19, Vite, TypeScript, TailwindCSS, Leaflet, Three.js.

## NASA Data
- NASA JPL Small-Body Database (SBDB) `https://ssd-api.jpl.nasa.gov/sbdb_query.api` (PHA summary)
- NASA JPL Small-Body Database (SBDB) `https://ssd-api.jpl.nasa.gov/sbdb.api` (object detail, orbit elements)
- NASA CNEOS impact monitoring concepts inspired crater/energy modelling (Purdue Impact Earth equations adapted for this tool)

Explain exactly how you used each dataset (e.g., "SBDB summary populates the asteroid search table; SBDB detail feeds kinetic energy and VI timeline; orbit elements drive the 3D viewer").

## Space Agency Partner & Other Data
- OpenTopoData ETOPO1 (NOAA/NGDC) - elevation, slope, roughness, and ocean depth
- OpenStreetMap Nominatim - landform category and ISO country code
- World Bank EN.POP.DNST indicator - country-level population density fallback
- Plotly.js, React Three Fiber, Leaflet basemap tiles (CartoDB Dark Matter)

List any additional imagery, fonts, code snippets, or libraries you include. Provide attribution or licenses if required.

## Use of Artificial Intelligence
AI tools used: <codex>


## Project Submission Verification
Confirm that you reviewed the Participant Terms & Conditions, Privacy Policy, and originality requirements. Ensure the public links are accessible without authentication before hitting **Submit for Judging**.

