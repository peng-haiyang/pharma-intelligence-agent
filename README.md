# Japan Pharma Intelligence Agent

A public-data, portfolio-grade pharmaceutical commercial intelligence agent, evolving from the Japan Market & Launch Outlook prototype.

**Stage:** 3B — verified public Japan evidence, read-only MCP stdio tools, and a bounded deterministic orchestration harness. Evidence only; no LLM answer synthesis or autonomous planner.

See [MCP setup](docs/stage3a-mcp.md) and [Stage 3B usage, tests and limitations](docs/stage3b-agent.md).

See [Stage 2C setup, sources, and limitations](docs/stage2c.md). Use `/api/v2/questions` for verified evidence; `/api/v1/questions` is the legacy unverified baseline.

## Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for API documentation.

## Test

```bash
cd backend
PYTHONPATH=. pytest -q
```

## Repository layout

- `backend/app/` — API and future agent services
- `backend/tests/` — automated tests
- `frontend/` — reserved for migration of original Japan UI
- `docs/migration-plan.md` — recovery status and feature parity plan
- `.github/workflows/ci.yml` — continuous integration

Original Japan site: https://gsk-japan-market-outlook.politecedar3.chatgpt.site

**Disclaimer:** Independent technical demonstration, not affiliated with or endorsed by any pharmaceutical company. Public or synthetic data only. Not medical advice or a promotional recommendation.
