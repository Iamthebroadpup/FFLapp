# DraftHelper API (FastAPI)

## Windows Quick start
```
cd backend
copy .env.example .env
# Edit .env and set your SPORTS DATA key
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Initialize:
```
http://localhost:8000/api/init?season=2025&season_type=REG
```
Notes:
- Pulls season-long **Player** projections (QB/RB/WR/TE/**K**) and **DST** projections (separate feed).
- ADP merged from `stats/json/FantasyPlayers` (includes DST & K ADP when available).
