# Regulatory Intelligence

Daily regulatory news from **official government and regulator sources** for crypto, tech, and AI across selectable jurisdictions.

## Run locally (anyone on your network)

```powershell
cd "d:\cursor projects\regulatory-intelligence"
powershell -ExecutionPolicy Bypass -File scripts\start-public.ps1
```

Open **http://127.0.0.1:8080** (or `http://<your-computer-ip>:8080` from other devices on the same Wi‑Fi).

Admin panel: **http://127.0.0.1:8080/admin**

---

## Run with Docker (recommended for a VPS)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```powershell
cd "d:\cursor projects\regulatory-intelligence"
docker compose up --build -d
```

Public URL on the server: **http://YOUR_SERVER_IP:8080**

To use a custom domain, put Nginx or Caddy in front and point DNS to your server.

---

## Deploy to the public internet (Render — free tier)

**Full walkthrough:** see [DEPLOY-RENDER.md](DEPLOY-RENDER.md)

Quick summary:

1. Install Git: https://git-scm.com/download/win
2. Create repo on GitHub: https://github.com/new
3. Push the project (commands in DEPLOY-RENDER.md)
4. Render → **New → Blueprint** → connect repo → **Apply**
5. After deploy, open `/admin` and click **Run ingestion now**

Your public URL will look like: `https://regulatory-intelligence-xxxx.onrender.com`

---

## First-time local setup (manual)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python backend\seed.py
uvicorn backend.app.main:app --host 0.0.0.0 --port 8080
```

---

## Features

- Official source registry (US, SG, HK, UAE, Africa, EU)
- Filterable public feed by jurisdiction and topic
- Email digest signup and preview
- Admin health monitoring at `/admin`

## Scheduled jobs

```powershell
python -m backend.app.jobs.runner ingest
python -m backend.app.jobs.runner digest
```

## Tests

```powershell
pytest
```
