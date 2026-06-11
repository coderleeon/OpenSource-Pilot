# OpenSourcePilot

AI-powered open-source contribution assistant that helps developers understand GitHub issues, locate relevant code, generate contribution plans, create tests, and draft pull requests.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Next.js](https://img.shields.io/badge/Next.js-Frontend-black)
![Tests](https://img.shields.io/badge/Tests-209%2B-success)
![Deployment](https://img.shields.io/badge/Deployment-Railway%20%7C%20Vercel-purple)

## Live Links

- Frontend: https://open-source-pilot.vercel.app/
- API Docs: https://web-production-5369f.up.railway.app/docs
- GitHub: https://github.com/coderleeon/OpenSource-Pilot

## Overview

OpenSourcePilot analyzes a GitHub repository and issue, retrieves the relevant code context using semantic search, and generates actionable contribution guidance.

Instead of manually exploring large repositories, developers can quickly understand:

* What the issue is about
* Which files are relevant
* How to approach the solution
* What tests should be written
* What the final pull request could look like

## Features

### Repository Intelligence

* GitHub repository analysis
* Repository structure parsing
* Technology stack detection
* Repository metadata extraction

### Issue Understanding

* GitHub issue retrieval
* Issue classification
* Difficulty estimation
* Contributor suitability scoring
* Beginner-friendly issue detection

### Semantic Code Search

* ChromaDB vector indexing
* Sentence-transformer embeddings
* Relevant file discovery
* Semantic code retrieval

### Contribution Planning

* Step-by-step implementation plans
* Root cause analysis
* Recommended solution approach
* Contributor guidance

### Automated Test Generation

Supports:

* pytest
* Jest
* JUnit
* Go testing
* Rust testing

Generates:

* Unit tests
* Integration tests
* Edge-case coverage

### Pull Request Drafting

Generates:

* PR title
* Summary
* Reviewer notes
* Testing checklist
* Labels
* Complete markdown PR description

### Complete Workflow Execution

Single API call performs:

1. Repository analysis
2. Issue retrieval
3. Issue classification
4. Semantic search
5. Contribution planning
6. Test generation
7. PR drafting

## Architecture

```text
Frontend (Next.js)
        │
        ▼
FastAPI Backend
        │
        ▼
Contribution Workflow Service
        │
 ┌──────┼─────────────┐
 ▼      ▼             ▼
Repo   Issue      Planning
Agent  Agent       Agent
 │       │           │
 ▼       ▼           ▼
GitHub  Search    LLM Layer
API     Engine
        │
        ▼
     ChromaDB
```

## Tech Stack

### Frontend

* Next.js
* TypeScript
* Tailwind CSS

### Backend

* FastAPI
* Python

### AI & Retrieval

* OpenRouter
* OpenAI
* Anthropic
* ChromaDB
* sentence-transformers
* all-MiniLM-L6-v2

### GitHub Integration

* PyGithub
* GitPython

### Testing

* Pytest

### Deployment

* Railway
* Vercel

### Frontend

https://open-source-pilot.vercel.app/

### Backend API Documentation

https://web-production-5369f.up.railway.app/docs

## Quick Start

### Clone Repository

```bash
git clone https://github.com/coderleeon/OpenSourcePilot.git
cd OpenSourcePilot
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment

```env
OPENROUTER_API_KEY=your_key
GITHUB_TOKEN=your_token
LLM_PROVIDER=openrouter
OPENROUTER_MODEL=anthropic/claude-3.5-haiku
```

### Run Backend

```bash
uvicorn app.main:app --reload
```

### Run Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### Repository Analysis

```http
POST /api/v1/repo/analyze
```

### Issue Analysis

```http
POST /api/v1/issue/analyze
```

### Issue Listing

```http
POST /api/v1/issue/list
```

### Semantic Code Search

```http
POST /api/v1/search/code
```

### Complete Workflow

```http
POST /api/v1/issue/complete-workflow
```

Example:

```json
{
  "repo_url": "https://github.com/pallets/flask",
  "issue_number": 5400
}
```

## Testing

Run all tests:

```bash
pytest -v
```

Current Status:

* 209+ tests passing

## Example Workflow

Input:

```text
Repository:
https://github.com/pallets/flask

Issue:
5400
```

Output:

* Issue classification
* Repository metadata
* Relevant files
* Semantic search results
* Contribution plan
* Generated tests
* Pull request draft

## Screenshots

Add screenshots of:

* Dashboard
* Workflow execution
* Contribution plan
* Generated tests
* PR draft

## Roadmap

### Completed

* Repository analysis
* Issue analysis
* Semantic code search
* Contribution planning
* Test generation
* PR drafting
* Complete workflow orchestration
* Web interface
* Railway deployment
* Vercel deployment

### Future Improvements

* Repository health reports
* Good-first-issue recommendations
* Contributor readiness scoring
* Workflow caching
* Advanced repository analytics

## Author

Leeon John

Twitter - https://x.com/LeeonJohn_

GitHub:
https://github.com/coderleeon


LinkedIn:
https://www.linkedin.com/in/leeon-john-14172a159/
