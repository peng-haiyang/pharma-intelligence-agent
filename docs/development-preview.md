# Development workbench and preview

The original site at https://gsk-japan-market-outlook.politecedar3.chatgpt.site
is untouched. This repository's `frontend/` is a new workbench, not recovered
original source and not a claim of feature parity.

## What is visible now

- Evidence desk: English/Japanese snapshots of the three reviewed summaries,
  direct publisher URLs, review dates and content hashes.
- Evaluation lab: stored real semantic report, metrics and all gold-labelled
  cases, filterable by expected behavior. Gold references are authored labels,
  never presented as model answers.
- Build journal: original prototype, Stages 1, 2C, 3A, 3B, 4A and proposed next
  work. These are milestone descriptions, not simulated historical deployments.

The static preview has no backend or live pharma data. It makes no inference and
sends no benchmark questions externally. It never substitutes mocked answers for
a live service. The backend mode uses same-origin `/api/v2/questions` and returns
real evidence or explicit unavailable/insufficient-evidence results. No CORS
wildcards, browser secrets or third-party API keys are needed.

## Local preview and real backend

From repository root, build and serve the static snapshot:

```bash
python scripts/build_demo.py
python -m http.server 8765 --directory dist
```

Open `http://127.0.0.1:8765/`. For real queries, install backend requirements,
re-ingest a scratch verified index using the existing ingestion script, set
`PHARMA_VERIFIED_DB` to its absolute path, then run:

```bash
PYTHONPATH=backend uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/demo/`. Without an index this mode reports its missing
configuration. The static directory must exist before backend startup. The
backend does not run MCP orchestration for these UI queries; that remains a
separate tested interface. A production backend host needs Python, persistent
index storage, model cache, startup ingestion, and measured cold-start budgets.
Static hosting alone cannot provide these services.

## Hosted path and future updates

The chosen path is a **separate owner-private Sites application**, with its own
source repository and Site identity. Static hosting is sufficient for the current
source browser, report inspector and journal. The original Site identity is never
used. This avoids changing repository-wide GitHub Pages settings or deploying
unmerged backend code publicly. Sign in with the owning ChatGPT account to view it.

GitHub Actions builds a downloadable `development-demo-<commit>` artifact on
push/PR; this artifact is not itself a deployed website. GitHub Pages is a viable
alternative after explicit repository hosting setup: publish the built `dist/`
directory through a Pages workflow with a protected environment. No Pages URL is
claimed until an actual deployment succeeds.

To evolve this preview at each stage: update the UI and journal together, run
backend and browser checks, regenerate the stored report when retrieval changes,
build `dist/`, then publish a new version to the same development Site. Keep the
Site version and corresponding GitHub commit in the release record; previous
Site versions support reviewing older deployed states. CI artifacts preserve a
static package for each commit; hosted updates are deliberate, not automatically
published by this PR. A PR link is the source review path, separate from the demo.

Do not expose a backend until authentication, rate/resource limits, cache/storage,
source update policy and operational monitoring are implemented. This is a
technical demonstration with only existing approved public summaries and
synthetic benchmark questions; no internal company or patient information.

## Verified deployment — 31 October 2026

Development preview: https://pharma-intelligence-development.peng0041.chatgpt.site

Sites confirmed deployment `appgdep_6ae5c315491081918d2eb4d610ad9e39` succeeded.
It is owner-private; sign in with the account that owns the Site. Site project:
`appgprj_6ae5c1d106a08191a408073923906135`. Published version:
`appgprj_6ae5c1d106a08191a408073923906135~appgver_ae576aac80dc8191ab0eb8beb7cb0913`.
Its separate static source commit is `3df45d9818357c01ff5296cbaea53c28c681668b`.
This version contains the Stage 4A workbench and the pinned-model local report.
