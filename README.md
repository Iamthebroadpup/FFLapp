# FFLapp

Prototype modules for a fantasy football helper app.

## Project Structure

```
backend/    FastAPI application and data utilities
frontend/   React client served by Vite
scoring/    Fantasy scoring rules and calculators
utils/      Misc helper functions
```

## Launching the App

The project includes a FastAPI backend and a React frontend served by Vite. The following steps describe how to run the full stack in GitHub Codespaces.

### 1. Start the backend

Install Python dependencies and run the API server:

```bash
pip install -r requirements.txt
uvicorn backend.app:app --reload
```

The backend listens on port **8000**.

### 2. Start the frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite serves the app on port **5173**. Codespaces automatically forwards this port; open it from the **Ports** panel or accept the prompt to preview the site.

The frontend proxies requests under `/api` to the backend, so keep both processes running to use live data.

## Data Integration Outline

- `backend/ffn_api.py` wraps the Fantasy Football Nerd API (uses the `FFN_API_KEY` environment variable and defaults to the key `TEST`).
- `backend/nfl_data.py` fetches play-by-play data from the NFL fastR repository.
- `backend/data_service.py` demonstrates merging these sources into a single player pool loaded at server startup.

This skeleton sets up the draft state management and provides a minimal React UI that lists available players. Further features—such as custom scoring, draft recommendations, and advanced analytics—can be built on top of this foundation.
