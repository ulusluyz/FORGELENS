# ForgeLens — Technology Decision Record

## 1. Backend & Language Environment
- **Language:** Python 3.12+
- **Rationale:** Native support for modern typing features, high performance with `asyncio`, excellent ecosystem for API connectors and data processing.

## 2. Web Interface & Application Server
- **Framework:** FastAPI + Uvicorn
- **Rationale:** FastAPI provides lightweight, high-performance async REST API endpoints. The frontend is served as a local Web UI (HTML/CSS/JS) without relying on external cloud/hosted services.
- **Frontend:** Pure HTML5, CSS3, vanilla JavaScript (Fetch API, responsive layout).
- **Rationale:** Simple, standalone, no complex JS build steps (no Node/npm build pipeline needed), fast execution and low memory footprint.

## 3. CLI Framework
- **Framework:** Typer (built on Click & Rich)
- **Rationale:** Clear command-line structure, automatic argument parsing, rich console output for terminal audits.

## 4. HTTP Client & Async Networking
- **Library:** `httpx`
- **Rationale:** Supports both synchronous and asynchronous HTTP requests, streaming, custom timeouts, retry logic, and exponential backoff.

## 5. Storage & Local Persistence
- **Database:** Standard library `sqlite3`
- **Rationale:** Zero external dependencies, self-contained, transactional, portable database file (`~/.forgelens/forgelens.db`).

## 6. Template Engine
- **Library:** `jinja2`
- **Rationale:** Standard, safe rendering engine for generating HTML and Markdown audit reports.

## 7. Deterministic Language Detection
- **Library:** `langdetect`
- **Rationale:** Local, fast, lightweight language identification across sampling rows without incurring cloud AI API costs.

## 8. Testing Framework
- **Framework:** `pytest` + `pytest-asyncio`
- **Rationale:** Robust test runner with mock support for network and AI provider tests.
