# OpenSourcePilot Deployment Guide

This guide describes how to deploy **OpenSourcePilot** to [Railway](https://railway.app) with persistent storage and production-ready environment configuration.

---

## Prerequisites

- A GitHub account containing a fork or copy of the [OpenSourcePilot](https://github.com/coderleeon/OpenSourcePilot) repository.
- A Railway account linked to GitHub.
- An API Key for OpenRouter, OpenAI, or Anthropic (active provider).

---

## Step 1: Create a Railway Project

1. Log in to [Railway](https://railway.app).
2. Click **New Project** in the upper-right corner.
3. Select **Deploy from GitHub repo**.
4. Choose the `OpenSourcePilot` repository from your list.
5. Click **Deploy Now**.
   *Note: The first build might fail or be paused because we have not yet configured the environment variables or the persistent volume. This is expected.*

---

## Step 2: Configure Persistent Storage (Railway Volume)

OpenSourcePilot clones GitHub repositories locally and builds persistent ChromaDB vector databases. Since Railway container file systems are ephemeral, you **must** attach a persistent volume.

1. In the project canvas, select your **OpenSourcePilot** service.
2. Go to the **Settings** tab.
3. Scroll down to the **Volumes** section and click **Add Volume**.
4. Configure the volume:
   - **Mount Path**: `/data`
   - **Size**: Select appropriate size (e.g., `5 GB` or `10 GB` is plenty for indexing dozens of average repos).
5. Click **Add Volume**.

This mounts a persistent disk to the `/data` directory in your running container.

---

## Step 3: Configure Environment Variables

1. Select your service in Railway and go to the **Variables** tab.
2. Add the environment variables specified in the reference below.

### Production Environment Variables Reference

| Variable | Description | Required? | Default/Value |
|---|---|---|---|
| `PORT` | Managed automatically by Railway. | Yes | (Auto-managed) |
| `LLM_PROVIDER` | Chosen LLM provider: `openrouter`, `openai`, or `anthropic`. | No (Defaults) | `openrouter` |
| `OPENROUTER_API_KEY` | OpenRouter API Key. Required if provider is `openrouter`. | Optional | `sk-or-...` |
| `OPENROUTER_MODEL` | OpenRouter model slug. | No | `anthropic/claude-3.5-haiku` |
| `OPENAI_API_KEY` | OpenAI API Key. Required if provider is `openai`. | Optional | `sk-proj-...` |
| `OPENAI_MODEL` | OpenAI model identifier. | No | `gpt-4o-mini` |
| `ANTHROPIC_API_KEY` | Anthropic API Key. Required if provider is `anthropic`. | Optional | `sk-ant-...` |
| `ANTHROPIC_MODEL` | Anthropic model identifier. | No | `claude-3-5-haiku-20241022` |
| `GITHUB_TOKEN` | GitHub Personal Access Token (for issues/repo metadata fetching). | **Strongly Recommended** | `ghp_...` (avoids rate limits) |
| `CHROMA_PERSIST_DIR` | Directory where ChromaDB indexes are stored on the disk. | **Yes** (set to Volume) | `/data/chroma_db` |
| `CLONE_BASE_DIR` | Directory where cloned repositories are stored on the disk. | **Yes** (set to Volume) | `/data/repos` |
| `LOG_LEVEL` | Log verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. | No | `INFO` |
| `LOG_FORMAT` | Format style: `json` (for structured log processors) or `console`. | No | `json` |

Make sure `CHROMA_PERSIST_DIR` and `CLONE_BASE_DIR` are nested inside the mounted persistent path `/data` so they survive service restarts and deploys.

---

## Step 4: Trigger First Deployment

1. Once the variables and volume are configured, Railway will automatically queue a new deployment.
2. If it does not trigger automatically, go to the **Deployments** tab and click **Redeploy**.
3. Wait for the Nixpacks builder to compile dependencies and start the Uvicorn web process.

---

## Step 5: Verification

### 1. Health Check
OpenSourcePilot implements a readiness health check. Check it by visiting:
```text
https://<your-app-domain>.up.railway.app/health
```
It must return a `200 OK` status with the body:
```json
{
  "status": "healthy"
}
```
*Note: If the health check returns `503 Service Unavailable`, review your logs to check if the LLM provider API key is missing, or if the persistent directories (/data/chroma_db or /data/repos) are missing write permissions.*

### 2. Swagger Documentation
Interactive Swagger docs are mounted at:
```text
https://<your-app-domain>.up.railway.app/docs
```
You can execute example queries (such as semantic search or contribution planning requests) directly in the browser.
