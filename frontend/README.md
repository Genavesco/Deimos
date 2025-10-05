# DEIMOS Frontend

This directory contains the Vite + React single-page application for the DEIMOS impact simulator.

## Available Scripts
- `npm run dev -- --host` -- start the development server at http://127.0.0.1:5173
- `npm run build` -- produce a production build in `dist/`
- `npm run preview` -- serve the production build locally
- `npm run lint` -- run ESLint checks

## Environment
The frontend expects the backend API at `http://127.0.0.1:8000/api` (see `src/lib/api.ts`). If you deploy the API elsewhere, update that base URL or wire Vite's proxy settings.

Refer to the repository-level `README.md` for full setup instructions and submission checklists.
