# Deploy to Render (Option A)

Follow these steps to get a public URL like `https://regulatory-intelligence.onrender.com`.

## Step 1 — Install Git (one time)

Git is not installed on your PC yet. Install it:

1. Download **Git for Windows**: https://git-scm.com/download/win
2. Run the installer (defaults are fine)
3. **Close and reopen** PowerShell/Cursor after installing

Verify:
```powershell
git --version
```

**Alternative:** use [GitHub Desktop](https://desktop.github.com/) if you prefer a visual app.

---

## Step 2 — Push code to GitHub

### A) Create a GitHub repository

1. Go to https://github.com/new
2. Repository name: `regulatory-intelligence`
3. Set to **Public** (required for Render free tier)
4. Do **not** add README, .gitignore, or license (we already have them)
5. Click **Create repository**

### B) Push from your project folder

Open PowerShell:

```powershell
cd "d:\cursor projects\regulatory-intelligence"

git init
git add .
git commit -m "Initial commit: regulatory intelligence MVP"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/regulatory-intelligence.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

GitHub will ask you to sign in (browser or personal access token).

---

## Step 3 — Deploy on Render

1. Go to https://render.com and sign up (use **Sign in with GitHub**)
2. Click **New +** → **Blueprint**
3. Connect your GitHub account if prompted
4. Select the `regulatory-intelligence` repository
5. Render detects `render.yaml` automatically
6. Click **Apply**

Render creates:
- A **Web Service** (Docker)
- A **PostgreSQL** database (free tier)

First deploy takes **5–10 minutes**.

---

## Step 4 — After deploy

1. Open your Render dashboard → **regulatory-intelligence** web service
2. Copy the URL (e.g. `https://regulatory-intelligence-xxxx.onrender.com`)
3. Go to **Environment** and add:
   - `PUBLIC_URL` = your Render URL
4. Click **Manual Deploy → Deploy latest commit** (optional, to pick up env var)

### Load initial data

The site starts empty. After deploy:

1. Visit `https://YOUR-URL.onrender.com/admin`
2. Click **Run ingestion now**
3. Wait 1–2 minutes, then open the main site

### Optional: email digests

In Render **Environment**, add:
- `GMAIL_ADDRESS` — your Gmail
- `GMAIL_APP_PASSWORD` — [Google App Password](https://myaccount.google.com/apppasswords)
- `DEFAULT_DIGEST_EMAIL` — where test digests go

---

## Notes

- **Free tier cold starts:** the site sleeps after ~15 min idle; first visit may take 30–60 seconds to wake up.
- **Custom domain:** Render dashboard → Settings → Custom Domain.
- **Redeploy:** push to GitHub `main`; Render auto-deploys.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Deploy fails health check | Check Logs; `/api/health` must return 200 |
| Empty feed | Run ingestion from `/admin` |
| Database connection error | Ensure `render.yaml` was applied as Blueprint (not manual web service only) |
| Git not found | Reinstall Git and restart terminal |
