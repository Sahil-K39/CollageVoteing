# Collage Voting (FastAPI + Static UI)

A lightweight e-voting demo with a FastAPI backend (blockchain-based vote ledger) and a static HTML/JS frontend.

## Run locally
```bash
# backend
cd "blockchain_voting"
uvicorn main:app --reload --host 127.0.0.1 --port 8300

# frontend (static)
cd "../static_frontend"
python3 -m http.server 3102
# open http://127.0.0.1:3102 (API auto-points to http://127.0.0.1:8300 when on localhost)
```

## Deploy backend to Render (free)
- Ensure `Procfile` exists (already included):
  ```
  web: uvicorn blockchain_voting.main:app --host 0.0.0.0 --port $PORT
  ```
- In Render: New Web Service → connect repo → build command `pip install -r requirements.txt` → start command above → free instance.
- Backend URL will be like `https://yourapp.onrender.com`.

## Serve UI
Option A (same origin): Render can serve `/ui` because `main.py` mounts `static_frontend` at `/ui` if present.

Option B (Netlify):
1) `static_frontend/index.html` auto-uses same origin when not on localhost; set API line if needed. 
2) Deploy `static_frontend/` to Netlify (publish directory `static_frontend`, no build command).

## Demo credentials
- Admin: `admin123` / `admin_secure_password`
- Voters: DEMO01..DEMO05 with passwords `Vote@123`, `Vote@234`, `Vote@345`, `Vote@456`, `Vote@567`

## Data
JSON seed files live in `blockchain_voting/data/`. Free Render instances lose local files on redeploy; for persistence add a disk or move to a DB later.

