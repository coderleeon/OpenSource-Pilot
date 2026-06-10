# OpenSourcePilot — Vercel Deployment Guide

Follow this guide to deploy the Next.js contributor dashboard frontend to Vercel. Since this frontend application is located within a monorepo subdirectory (`frontend`), specific directory parameters are required during Vercel import.

---

## Prerequisites
1. A deployed **OpenSourcePilot backend** (e.g., hosted on Railway).
2. The URL of the deployed backend API (e.g., `https://opensourcepilot-backend.up.railway.app`).

---

## Step-by-Step Vercel Setup

### 1. Import Repository
1. Log in to your [Vercel Dashboard](https://vercel.com).
2. Click **Add New** ➔ **Project**.
3. Import the `OpenSourcePilot` repository from GitHub.

### 2. Configure Project Settings
In the **Configure Project** screen, expand the settings and configure the following parameters:

- **Project Name**: `opensourcepilot-dashboard` (or preferred name)
- **Framework Preset**: `Next.js`
- **Root Directory**: Click **Edit** and select the `frontend` folder (or type `frontend`).
- **Build and Development Settings**:
  - Keep the default settings (Vercel automatically detects Next.js build scripts when Root Directory is set).
  - *Build Command*: `next build`
  - *Output Directory*: `.next`
  - *Install Command*: `npm install`

### 3. Configure Environment Variables
Expand the **Environment Variables** section and configure the backend URL link:

| Key | Value | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://your-backend-api-url.railway.app` | The production URL of your FastAPI backend (exclude trailing slashes). |

> [!IMPORTANT]
> The environment variable prefix `NEXT_PUBLIC_` is required by Next.js to expose variables to the browser/client-side fetch calls. If not provided or set incorrectly, API calls will fail at client-side runtime.

### 4. Deploy
1. Click **Deploy**.
2. Vercel will install dependencies, compile the TypeScript pages, build static assets, and assign a production domain name (e.g., `https://opensourcepilot-dashboard.vercel.app`).

---

## CORS Considerations
The FastAPI backend contains global CORS configurations that permit requests from any origin (`allow_origins=["*"]`). If you decide to restrict origins in the backend settings for safety:
1. Locate `app/main.py` in the backend codebase.
2. Edit `allow_origins` to include your new Vercel domain:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "https://opensourcepilot-dashboard.vercel.app",
           "http://localhost:3000",
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```
3. Re-deploy the backend service.
