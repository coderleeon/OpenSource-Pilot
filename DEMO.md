# OpenSourcePilot — Demo Scenarios Registry

Use these 5 curated repository and issue scenarios to demonstrate and evaluate OpenSourcePilot. They are selected to showcase the engine's core capabilities in bug classification, vector database matching, step planning, pytest suite synthesis, and Q&A branching.

---

## Curated Demo Scenarios

### Scenario 1: Pallets Flask (Bug Resolution)
- **Repository**: `https://github.com/pallets/flask`
- **Issue Number**: `5420`
- **Focus Area**: Classifying bugs in web frameworks.
- **What it showcases**:
  - **Issue Classification**: Recognizes routing/server bugs.
  - **Code Discovery**: Vector search matches against Flask application logic and routing parameters.
  - **Test Suite**: Generates standard unit tests verifying Flask endpoints.

---

### Scenario 2: PSF Requests (Feature/Adapter Integration)
- **Repository**: `https://github.com/psf/requests`
- **Issue Number**: `6000`
- **Focus Area**: HTTP sessions and connection adapters.
- **What it showcases**:
  - **Suitability Assessment**: Renders difficulty levels for third-party client APIs.
  - **Planning**: Outlines clear step-by-step instruction blocks detailing how connection pools are configured.
  - **PR Description**: Builds review checklists highlighting network testing requirements.

---

### Scenario 3: Pytest-Dev Pytest (Edge Case Logic)
- **Repository**: `https://github.com/pytest-dev/pytest`
- **Issue Number**: `11000`
- **Focus Area**: Advanced framework assertion helper mechanisms.
- **What it showcases**:
  - **Codebase Indexing**: Indexes complex tree elements (assertions, runner configurations).
  - **Planning**: Displays specialized python-specific code changes.
  - **Test Suite**: Synthesizes mock environments and error paths.

---

### Scenario 4: Django Django (Large-Scale Codebase Discovery)
- **Repository**: `https://github.com/django/django`
- **Issue Number**: `16000`
- **Focus Area**: High-performance semantic code indexing limits.
- **What it showcases**:
  - **ChromaDB Vector Store**: Demonstrates that the sentence-transformers model indexer handles deep class structures efficiently.
  - **Relevant Files**: Isolates specific ORM or database adapter models within a codebase containing thousands of files.

---

### Scenario 5: Pallets Click (Q&A / Discussion Branching)
- **Repository**: `https://github.com/pallets/click`
- **Issue Number**: `2500`
- **Focus Area**: Discussion triage and bypass pipeline.
- **What it showcases**:
  - **Adaptive Branching**: Classifies the issue as a question/discussion.
  - **Bypass Logic**: Skips the expensive code cloning and vector indexing.
  - **Answer Synthesis**: Outputs structured explanations, references, suggested resources, and key questions instead of code edits.
