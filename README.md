# Japan Pharma Intelligence Agent

A public-data, portfolio-grade pharmaceutical commercial intelligence agent, evolving from the Japan Market & Launch Outlook prototype.

**Stage:** 1 — API scaffold and tests. RAG, MCP and LLM integration are not yet implemented.

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
