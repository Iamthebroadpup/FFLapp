# FFLapp

Prototype full‑stack modules for a fantasy football helper app.

## Overview

The backend ingests data from public APIs and play‑by‑play releases to build a
player pool, and the frontend renders a simple list of available players. The
project is meant to serve as a starting point for a personalized draft
assistant that can run entirely on your machine during an in‑person draft.

## Project Structure

```
backend/    FastAPI application and data utilities
frontend/   React client served by Vite
scoring/    Fantasy scoring rules and calculators
utils/      Misc helper functions
```

## Launching the App

The project includes a FastAPI backend and a React frontend served by Vite. To
run both pieces locally:

1. **Start the backend**

   ```bash
   pip install -r requirements.txt       # install Python dependencies
   uvicorn backend.app:app --reload      # start FastAPI on http://localhost:8000
   ```

2. **Start the frontend** in a separate terminal

   ```bash
   cd frontend
   npm install                           # install JS dependencies
   npm run dev                           # start Vite on http://localhost:5173
   ```

Codespaces forwards port **5173** automatically. When developing locally, open
the URL printed by Vite in your browser. The frontend proxies `/api` requests to
the backend, so keep both processes running for live data.

### Using the App

Visiting the frontend displays a list of players fetched from the backend. You
can refresh the list at any time by clicking **Refresh Players** in the UI.
This minimal interface provides a foundation for more advanced draft tools.

## Data Integration Outline

- `backend/ffn_api.py` wraps the Fantasy Football Nerd API (uses the `FFN_API_KEY` environment variable and defaults to the key `TEST`).
- `backend/nfl_data.py` fetches play-by-play data from the nflverse data release (stored as `.parquet`).
- `backend/data_service.py` demonstrates merging these sources into a single player pool loaded at server startup.

This skeleton sets up the draft state management and provides a minimal React UI that lists available players. Further features—such as custom scoring, draft recommendations, and advanced analytics—can be built on top of this foundation.

## Future Enhancements for In‑Person Drafts

To turn this prototype into a full draft assistant for use with a physical
whiteboard, consider adding:

- **Clickable Draft Board** – allow selecting players in the UI to mark them as
  drafted and assign them to specific teams.
- **Roster Tracking** – display each team's roster, remaining positional needs,
  and bye weeks.
- **Recommendation Engine** – use projections, positional scarcity, and roster
  construction to suggest the best pick for your upcoming turn.
- **Offline Data Cache** – bundle player data so the app can run without an
  internet connection during an in‑person draft.
- **Export/Import State** – save the draft board to disk and reload it later to
  resume or review the draft.

These improvements would enable the app to predict optimal picks and keep track
of selections as you click players off the board in real time.
