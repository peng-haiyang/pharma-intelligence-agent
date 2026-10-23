# Stage 2C: verified Japan public evidence

The new `POST /api/v2/questions` endpoint integrates multilingual Chroma retrieval
with a reviewed corpus. The legacy `/api/v1/questions` endpoint remains an
unverified demonstration baseline; do not use it for evidence-backed conclusions.

## Run

From `backend/`, install `requirements-rag.txt`, then:

```sh
python -m scripts.ingest_verified --db ../.chroma
PHARMA_VERIFIED_DB=../.chroma uvicorn app.main:app --reload
```

The explicit ingestion step can download the multilingual MiniLM model. Runtime
retrieval may also download it if its cache is absent. Set `HF_HUB_OFFLINE=1` for
an offline deployment after provisioning the model. Do not expose this demo
publicly without authentication, rate limits, and deployment review.

Example request: `{"question":"COPD smoking cessation inhaled bronchodilators"}`.
The response returns validated citations or an explicit abstention reason.
`answer` is always null and `synthesis` is disabled. This intentionally implements
the abstention option, rather than treating semantic similarity as claim support.
The default cosine distance cutoff 0.35 is conservative but **not calibrated**.
A retrieved passage is not evidence that every part of a question is answerable.

## Corpus and provenance

Three short original bilingual factual summaries were checked against the direct
public HTML sources on 2026-10-23:

- [PMDA patient reports overview](https://www.pmda.go.jp/safety/reports/patients/0030.html), section 情報の活用について.
- [MHLW appropriate use of medicines](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iyakuhin/topics/index_00003.html), sections 安全対策の必要性 and 副作用等の報告.
- [Japanese Respiratory Society COPD overview](https://www.jrs.or.jp/citizen/disease/b/b-01.html), section 治療.

These are public information documents, not full clinical guidelines. No
subscription/member-only guideline, drug label, or raw adverse event report is
redistributed. The manifest records publisher, exact URL, section, language,
verification/access dates, review method, rights note, and SHA-256 of each local
summary. Publication dates are null because a reliable date was not established;
access dates are not publication dates. Summaries are editorial translations,
not official translations. Source copyright remains with the publishers; public
access does not establish a redistribution license. The repository license does
not relicense source documents. No raw HTML snapshot is committed; the content
hash verifies the local summary, not the remote page.

## Safety and versioning

Ingestion reads only manifest-listed local UTF-8 text, validates the entire corpus
before DB access, and rejects traversal, symlinks, oversized files, modified
content, unsupported origins and missing provenance. There is no crawler, URL
fetcher, upload endpoint, or executable document parser, so source URLs cannot
trigger SSRF. Manual review remains necessary: hashes and approved domains do
not prove truth, privacy compliance, or license clearance for future documents.
Treat all source text as data. No LLM or tool executes document instructions.

Collection names incorporate all validated metadata, passages, chunker version,
and model identity. Corpus edits require explicit re-ingestion; obsolete
collections are ignored, not deleted automatically. A partial/missing index
causes abstention. Citations resolve from the validated corpus, never arbitrary
DB metadata/text. Exceptions are logged server-side; API responses do not expose
local paths. Chroma and model revisions are not locked, so rebuilds can differ.

## Validation and limits

Normal PR CI runs deterministic corpus, security, vector adapter, API and legacy
tests on Python 3.11 and 3.13, without downloading models. A manual
`workflow_dispatch` also runs a real multilingual model/Chroma ingestion and
retrieval smoke test. That smoke test is not a labelled relevance evaluation.
The corpus is deliberately small, with no drug-specific positioning, NHI pricing,
launch timing, completeness guarantee, live refresh, generative synthesis, or
medical advice. Production use needs larger reviewed coverage, Japanese/English
labelled retrieval and abstention evaluation, pinned model revisions, and source
change/review processes.
