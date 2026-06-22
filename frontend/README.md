# OpenSourcePilot — Contributor Dashboard Web App

A Next.js + TypeScript + Tailwind CSS dashboard providing visual support for OpenSourcePilot Phase 5 agentic contributor pipelines, including Open Source Radar opportunity discovery, repository structure exploration, health audits, solution planning, and PR generation workflows.


---

## Local Development Guide

### Prerequisites
1. **Node.js**: Version 18.x or 20.x+ (Recommended)
2. **Python**: Version 3.10 to 3.12+ (For the backend server)

---

### Step 1: Start the Backend Service
The frontend relies on the FastAPI server to query indexing metadata, plan contributions, generate tests, and draft PR metrics.

1. Navigate to the project root directory.
2. Activate your virtual environment and start uvicorn:
   ```powershell
   # On Windows PowerShell
   .venv\Scripts\activate
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
3. The API documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) and the server will bind to CORS requests.

---

### Step 2: Start the Frontend App
1. Open a new terminal in the `frontend` directory:
   ```powershell
   cd frontend
   ```
2. Install npm dependencies (if not already done):
   ```bash
   npm install
   ```
3. Launch the development server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

### Environment Variables
By default, the React client points to the API server at `http://localhost:8000`. You can configure a different backend destination by adding a `.env.local` file in the `frontend` root:
```env
NEXT_PUBLIC_API_URL=https://your-custom-backend-url.railway.app
```

---

### Verifying a Production Build
To make sure TypeScript compilation and Next.js bundle building succeed:
```bash
npm run build
```
This command compiles static client components under `.next/` and ensures type validation passes with zero errors.
