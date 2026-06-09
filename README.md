# OpenSourcePilot

> AI-powered open-source contribution assistant.

Given a GitHub repository URL and an issue number, OpenSourcePilot clones the repository, semantically indexes its source code, retrieves the issue, and generates a detailed contribution plan, test suites, and pull request drafts — all through a clean FastAPI backend.

---

## Live Demo & Docs

- **Live Demo:** `https://your-app.up.railway.app`
- **Interactive Swagger Docs:** `https://your-app.up.railway.app/docs`

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/coderleeon/OpenSourcePilot
cd opensourcepilot
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set at minimum:
#   OPENROUTER_API_KEY=sk-or-v1-...
#   GITHUB_TOKEN=ghp_...      (optional but recommended)
```

### 3. Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive API docs.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/health` | Health check (readiness checking) |
| `POST` | `/api/v1/repo/analyze` | Analyse a GitHub repository |
| `POST` | `/api/v1/issue/list` | List & rank open issues |
| `POST` | `/api/v1/issue/analyze` | Analyse a specific issue |
| `POST` | `/api/v1/issue/generate-tests` | Generate unit, integration, and edge-case tests |
| `POST` | `/api/v1/issue/generate-pr-draft` | Generate a conventional commit PR title and description |
| `POST` | `/api/v1/issue/complete-workflow` | Run the complete end-to-end contribution pipeline |
| `POST` | `/api/v1/search/code` | Perform a local semantic code search |

### Execute complete contribution workflow

```bash
curl -X POST http://localhost:8000/api/v1/issue/complete-workflow \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/pallets/flask", "issue_number": 5420}'
```

---

## Project Structure

```
app/
├── main.py               # FastAPI app factory & lifespan (DI wiring)
├── config.py             # Settings via pydantic-settings
├── api/                  # HTTP layer (schemas + endpoints)
│   ├── deps.py           # FastAPI Depends providers
│   └── v1/
│       ├── schemas/      # Pydantic request/response models
│       └── endpoints/    # Thin route handlers
├── services/             # Workflow orchestration
├── agents/               # Domain logic
│   ├── repo_agent.py     # Clone · parse · metadata
│   ├── issue_agent.py    # Retrieve · rank issues
│   ├── code_analysis_agent.py  # Chunk · embed · search
│   ├── planning_agent.py       # LLM plans
│   ├── test_generation_agent.py # LLM framework-aware tests
│   ├── pr_agent.py             # LLM PR descriptions
│   └── contribution_workflow_agent.py # Unified agent coordinator
├── tools/                # External integrations
│   ├── git_tool.py       # GitPython wrapper
│   ├── github_api_tool.py # PyGithub wrapper
│   ├── structure_parser.py # Directory tree + tech stack
│   ├── code_chunker.py   # File → CodeChunk splitting
│   └── chroma_tool.py    # ChromaDB client
├── llm/                  # LLM abstraction
│   ├── base.py           # LLMClient ABC
│   ├── openrouter_client.py  # Default provider
│   ├── openai_client.py
│   ├── anthropic_client.py
│   └── factory.py
├── models/               # Pure domain dataclasses
└── core/                 # Exceptions · logging · middleware
```

---

## Deployment

For production deployment onto the **Railway** serverless cloud platform, see [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step instructions on project creation, persistent storage volume mounting, and environment variable references.

---

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openrouter` | LLM provider: `openrouter`, `openai`, `anthropic` |
| `OPENROUTER_API_KEY` | — | OpenRouter API key |
| `OPENROUTER_MODEL` | `anthropic/claude-3.5-haiku` | Model string |
| `GITHUB_TOKEN` | — | GitHub PAT (60 req/hr without) |
| `CLONE_BASE_DIR` | `./cloned_repos` | Where repos are cloned |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | ChromaDB persistence directory |
| `MAX_FILES_TO_INDEX` | `500` | Max source files per repo |
| `MAX_FILE_SIZE_KB` | `512` | Max file size to index |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Local sentence-transformers model |
| `LOG_LEVEL` | `INFO` | Log level |
| `LOG_FORMAT` | `console` | `console` or `json` |

---

## Running Tests

```bash
# Unit tests only (no network, fast)
pytest tests/unit/ -v

# Integration tests (mocked network, slightly slower)
pytest tests/integration/ -v -m integration

# All tests
pytest -v
```

---

## Phase Roadmap

| Phase | Status | Features |
|-------|--------|----------|
| 1 — MVP | ✅ Complete | Repo analysis · Issue discovery · Code indexing · Contribution plans |
| 2 — Enhanced | ✅ Complete | Test generation · PR drafting · Semantic code search |
| 3 — Production | ✅ Complete | Complete end-to-end workflow · Readiness healthchecks · Railway deployment configurations |
