# OpenSourcePilot

AI-powered open-source contribution workflow engine.

OpenSourcePilot helps developers understand and contribute to open-source projects by automatically analyzing repositories, understanding issues, retrieving relevant code, generating implementation plans, creating tests, and drafting pull requests.

Given a GitHub repository URL and an issue number, OpenSourcePilot produces a complete contribution package through a unified workflow endpoint.

---

## Features

### Repository Intelligence

* GitHub repository analysis
* Repository structure discovery
* Technology stack detection
* Repository metadata extraction
* Automated repository cloning

### Issue Understanding

* GitHub issue retrieval
* Issue classification
* Difficulty estimation
* Beginner-friendliness scoring
* Issue ranking and prioritization

Supported issue types:

* Bug
* Feature
* Documentation
* Question
* Discussion

### Semantic Code Search

* ChromaDB-powered vector search
* Sentence-transformers embeddings
* Relevant file discovery
* Context-aware code retrieval
* Semantic code snippet matching

### Contribution Planning

Generate detailed implementation plans including:

* Problem understanding
* Suggested approach
* Files to modify
* Implementation steps
* Validation strategy

### Framework-Aware Test Generation

Automatically generates tests for:

* pytest
* Jest
* JUnit
* Go testing
* Rust testing

Includes:

* Unit tests
* Integration tests
* Edge cases
* Failure scenarios

### Pull Request Draft Generation

Automatically generates:

* PR title
* Summary
* Testing checklist
* Reviewer notes
* Suggested labels
* Complete markdown PR description

### Contribution Workflow Engine

Single endpoint:

```http
POST /api/v1/issue/complete-workflow
```

Generates:

* Issue analysis
* Issue classification
* Relevant files
* Semantic search results
* Contribution plan
* Generated tests
* Pull request draft

---

## Workflow

```text
GitHub Repository
        │
        ▼
Repository Analysis
        │
        ▼
Issue Retrieval
        │
        ▼
Issue Classification
        │
        ▼
Semantic Code Search
        │
        ▼
Relevant File Discovery
        │
        ▼
Contribution Plan
        │
        ▼
Test Generation
        │
        ▼
Pull Request Draft
        │
        ▼
Complete Contribution Package
```

---

## Architecture

```text
Client
   │
   ▼
FastAPI API Layer
   │
   ▼
Services
   │
   ▼
Agents
   │
   ▼
Tools & Integrations
```

Architecture Pattern:

```text
API → Services → Agents → Tools
```

### Services

* RepoService
* IssueService
* SearchService
* ContributionWorkflowService

### Agents

* RepoAgent
* IssueAgent
* CodeAnalysisAgent
* PlanningAgent
* TestGenerationAgent
* PRAgent
* ContributionWorkflowAgent

### Integrations

* GitHub API (PyGithub)
* GitPython
* ChromaDB
* Sentence Transformers
* OpenRouter
* OpenAI
* Anthropic

---

## Tech Stack

### Backend

* FastAPI
* Pydantic
* AsyncIO

### LLM Providers

* OpenRouter
* OpenAI
* Anthropic

### Vector Search

* ChromaDB

### Embeddings

* sentence-transformers/all-MiniLM-L6-v2

### GitHub Integration

* PyGithub

### Git Operations

* GitPython

### Testing

* Pytest

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/coderleeon/OpenSourcePilot.git
cd OpenSourcePilot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxx
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx

LLM_PROVIDER=openrouter
OPENROUTER_MODEL=anthropic/claude-3.5-haiku
```

### 4. Run Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

```text
http://localhost:8000/docs
```

---

## API Endpoints

| Method | Endpoint                          | Description                    |
| ------ | --------------------------------- | ------------------------------ |
| GET    | `/health`                         | Health check                   |
| POST   | `/api/v1/repo/analyze`            | Analyze repository             |
| POST   | `/api/v1/issue/analyze`           | Analyze issue                  |
| POST   | `/api/v1/issue/list`              | List and rank issues           |
| POST   | `/api/v1/search/code`             | Semantic code search           |
| POST   | `/api/v1/issue/complete-workflow` | Complete contribution workflow |

---

## Example: Analyze Repository

```bash
curl -X POST http://localhost:8000/api/v1/repo/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/pallets/flask",
    "index_code": true
  }'
```

---

## Example: Analyze Issue

```bash
curl -X POST http://localhost:8000/api/v1/issue/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/pallets/flask",
    "issue_number": 5420
  }'
```

---

## Example: Semantic Search

```bash
curl -X POST http://localhost:8000/api/v1/search/code \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/pallets/flask",
    "query": "request context handling"
  }'
```

---

## Example: Complete Contribution Workflow

Request:

```bash
curl -X POST http://localhost:8000/api/v1/issue/complete-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/pallets/flask",
    "issue_number": 5420
  }'
```

Response:

```json
{
  "repository": {},
  "issue": {},
  "classification": {},
  "relevant_files": [],
  "search_results": [],
  "contribution_plan": {},
  "generated_tests": {},
  "pr_draft": {},
  "workflow_metadata": {
    "duration_ms": 1842
  }
}
```

---

## Project Structure

```text
app/
├── main.py
├── config.py
├── api/
│   ├── deps.py
│   └── v1/
│       ├── endpoints/
│       └── schemas/
├── services/
├── agents/
├── tools/
├── llm/
├── models/
└── core/

tests/
├── unit/
└── integration/
```

---

## Configuration

| Variable           | Description                   |
| ------------------ | ----------------------------- |
| LLM_PROVIDER       | openrouter, openai, anthropic |
| OPENROUTER_API_KEY | OpenRouter API key            |
| OPENAI_API_KEY     | OpenAI API key                |
| ANTHROPIC_API_KEY  | Anthropic API key             |
| GITHUB_TOKEN       | GitHub Personal Access Token  |
| CLONE_BASE_DIR     | Repository clone location     |
| CHROMA_PERSIST_DIR | ChromaDB storage location     |
| MAX_FILES_TO_INDEX | Maximum files indexed         |
| MAX_FILE_SIZE_KB   | Maximum file size             |
| EMBEDDING_MODEL    | Embedding model               |
| LOG_LEVEL          | Logging level                 |

---

## Testing

Run all tests:

```bash
pytest -v
```

Run unit tests:

```bash
pytest tests/unit -v
```

Run integration tests:

```bash
pytest tests/integration -v
```

Current Status:

```text
202+ Passing Tests
```

---

## Project Status

Version:

```text
v0.3.0
```

Completed Features:

* Repository Analysis
* Repository Cloning
* Repository Structure Parsing
* GitHub Issue Retrieval
* Issue Classification
* Semantic Code Search
* Contribution Planning
* Test Generation
* Pull Request Draft Generation
* Complete Workflow Orchestration

Quality Goals Achieved:

* Async-first architecture
* Dependency injection
* Service-agent-tool separation
* Multi-provider LLM support
* Structured logging
* Comprehensive automated testing

---

## Future Enhancements

Potential future directions:

* Repository readiness reports
* Contributor onboarding recommendations
* Good-first-issue recommendations
* Repository contribution scoring

---

## License

MIT License

---

## Author

Leeon John


Gmail- leeonjohn.work@gmail.com
LinkedIn: https://www.linkedin.com/in/leeon-john-14172a159/
