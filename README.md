# Fantasy Draft Assistant (SportsData.io)

Sleek, simple in-person draft helper. Tracks picks, shows suggestions, and adapts to league rules.
**Backend**: FastAPI (Python) — talks to SportsData.io **Frontend**: React + Vite (TypeScript)

> ⚠️ You need a SportsData.io NFL subscription + API key.
> Do **not** hardcode the key; set it via environment variable as shown below.

---

## Quick Start

### 1) Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # put your real key
# edit .env and set SPORTSDATA_API_KEY and SPORTSDATA_SEASON
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 2) Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

If your backend runs elsewhere, add `VITE_API_BASE=http://localhost:8000` to a `frontend/.env` file.

---

## What it uses
- **Players**: `/scores/json/PlayersByAvailable`
- **Bye Weeks**: `/scores/json/Byes/{season}`
- **Depth Charts**: `/scores/json/DepthChartsAll`
- **Projections w/ ADP**: we used `projections/json/PlayerSeasonProjectionStatsWithADP/{season}`.
  If your plan differs, adjust the path in `backend/providers/sportsdata.py`.

> The suggestor uses projected points + VORP baselines, with penalties for:
> committees, bye conflicts, and certain age curves. It adds a mild ADP bump.

---

## UI Tips
- **Drag & Drop** a player card into “Draft (ME)” or “Other Team” zones.
- Or click **Draft** / **Other** buttons on any player.
- Adjust **League Settings** in the left panel; suggestions update automatically.
- Search by name/team; filter by position from the top bar.

---

## Notes & Tweaks
- If projections endpoint 404s, open `backend/providers/sportsdata.py` and switch to another projections path consistent with your SportsData.io plan.
- The suggestor lives in `backend/logic/suggestor.py` — tweak the weights/penalties to taste.
- This repo intentionally favors clarity over hyper-optimized math so you can iterate fast during your draft prep.
