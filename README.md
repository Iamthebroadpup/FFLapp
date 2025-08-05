# FFLapp

Prototype modules for a fantasy football helper app.

## Project Structure

```
backend/    FastAPI application and data utilities
frontend/   React client served by Vite
scoring/    Fantasy scoring rules and calculators
utils/      Misc helper functions
```

## Dependencies

Backend requirements are listed in `requirements.txt` and include FastAPI and Uvicorn. The frontend uses React with Vite; see `frontend/package.json` for npm dependencies.

## Running the Backend

```bash
pip install -r requirements.txt
uvicorn backend.app:app --reload
```

## Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

## Data Integration Outline

- `backend/ffn_api.py` wraps the Fantasy Football Nerd API (requires an API key via `FFN_API_KEY`).
- `backend/nfl_data.py` fetches play-by-play data from the NFL fastR repository.
- `backend/data_service.py` demonstrates merging these sources into a single player pool loaded at server startup.

This skeleton sets up the draft state management and provides a minimal React UI that lists available players. Further features—such as custom scoring, draft recommendations, and advanced analytics—can be built on top of this foundation.
