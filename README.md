# Japan Pharma Intelligence Agent

A public-data, portfolio-grade pharmaceutical commercial intelligence agent, evolving from the Japan Market & Launch Outlook prototype.

**Stage:** 4A — bilingual evaluation framework and a separate development workbench, built on verified public evidence, read-only MCP tools, and bounded orchestration. Evidence only; no LLM answer synthesis or autonomous planner.

**Development preview:** [Open the evolving workbench](https://pharma-intelligence-development.peng0041.chatgpt.site) (owner-private; sign in). Original Japan site remains untouched.

See [Stage 4A benchmark, metrics, reproduction and limitations](docs/stage4a-evaluation.md) and [development preview and stage evolution](docs/development-preview.md).

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

Real model/index/MCP verification runs in the PR semantic-smoke CI job. See
[reproduction and coverage limits](docs/semantic-mcp-verification.md).

## Repository layout

- `backend/app/` — API and future agent services
- `backend/tests/` — automated tests
- `frontend/` — separate static development workbench; original site preserved
- `docs/migration-plan.md` — recovery status and feature parity plan
- `.github/workflows/ci.yml` — continuous integration

Original Japan site: https://gsk-japan-market-outlook.politecedar3.chatgpt.site

**Disclaimer:** Independent technical demonstration, not affiliated with or endorsed by any pharmaceutical company. Public or synthetic data only. Not medical advice or a promotional recommendation.
