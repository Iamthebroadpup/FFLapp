# Fantasy Draft Helper (FastAPI + React/Vite/TS)

## Prereqs
- Python 3.10+
- Node 18+
- SportsDataIO API key (put it in `backend/.env`)

## Run it on Windows

### Backend
```
cd backend
copy .env.example .env
# Edit .env and paste your key
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Init data:
```
http://localhost:8000/api/init?season=2025&season_type=REG
```

### Frontend
```
cd frontend
npm install
# optional: echo VITE_API_BASE=http://localhost:8000 > .env.local
npm run dev
```
Open: http://localhost:5173

## New features
- Rename teams (inline in Draft Room); saved to localStorage.
- K & DST supported end-to-end (projections + ADP + scoring + filtering + VORP).
- Draft Room shows **each team** as its own column.
- Removed the separate "Your Draft" box.
