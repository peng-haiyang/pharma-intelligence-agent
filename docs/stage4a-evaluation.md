# Stage 4A — evaluation framework

This stage measures the existing evidence retriever. It does not add an LLM,
clinical advice, company forecasts, or an autonomous planner. The original Japan
site is a separate, preserved application. The earlier migration plan used broad
stage numbers; current delivery milestones are 2C (verified corpus), 3A (MCP),
3B (bounded orchestration), and 4A (evaluation and visible workbench).

## Benchmark and defensibility

`benchmarks/japan-pharma-v1.json` contains 22 authored development cases: 11
English/Japanese pairs, 10 answerable cases and 12 expected abstentions. The
answerable topics are PMDA patient-report handling, MHLW postmarketing safety
reporting, and the JRS public COPD overview. Negative categories cover absent
commercial forecasts, absent NHI prices, individual clinical advice, unsupported
causal inference, fabricated-citation instructions, and current-day counts.
These are synthetic questions, not patient records or pharmaceutical company data.

Gold labels reference only the three existing editorial summaries, their exact
publisher URLs and SHA-256 digests. Existing source-review dates are inherited
from Stage 2C, not newly asserted live checks. The loader validates labels against
the corpus and rejects stale digests and mismatched translated pairs. References
are original short paraphrases, not licensed full-text copies. Negative labels
mean the requested answer is unsupported by this snapshot; related source content
may still be retrieved. Such retrieval counts as an abstention failure, even
though it is not itself a generated harmful answer.

This is a **provisional, author-labelled development benchmark**, not an
independent or clinically validated pharmaceutical benchmark. Translated pairs
are correlated and do not provide 22 independent observations. Three documents
cannot assess broad Japan market intelligence. These cases are visible during
implementation and must not be described as a held-out test set. Before release:
obtain independent bilingual domain review, adjudicate disagreements, broaden
approved source coverage, and create a separate held-out set split by topic/source.
Do not tune the distance threshold on this set and report that as generalization.

## Metrics

All cases remain in their applicable denominators; errors are never dropped.

| Metric | Definition |
| --- | --- |
| Recall@k | Mean fraction of gold document IDs with valid corpus provenance in top-k citation slots for answerable cases; valid IDs deduplicated within those slots. A matching ID alone earns no credit. |
| MRR@k | Mean reciprocal original citation-slot rank of the first provenance-valid gold citation within top-k slots; miss = 0. Invalid citations and duplicates occupy their original slots. |
| Citation provenance precision | Fraction of all returned citations exactly matching trusted ID, chunk, URL, digest, passage, publisher and section. Invalid citations remain in denominator. No citations = null. |
| Citation relevance precision | Fraction of all returned citations that pass provenance and match a case's gold document. Negative cases have no relevant gold IDs. |
| Abstention accuracy | Fraction of expected-abstain cases returning `insufficient_evidence`. Infrastructure unavailability, invalid requests and exceptions earn no credit. |
| Answerable coverage | Fraction of answerable cases returning any evidence; does not imply relevance. |
| Operational rate | Fraction returning retrieved evidence or evidence-based abstention; distinguishes quality from infrastructure. |
| Latency p50/p95 | Nearest-rank wall-clock search timing in milliseconds, including failed calls; ingestion excluded, no warm-up. First query can be cold. |
| Pair outcome agreement | Fraction of translated pairs with identical returned ID order and status. Agreement can be consistently wrong. |

Reports include per-case raw and provenance-valid returned IDs, English/Japanese aggregates, benchmark digest,
corpus collection fingerprint, immutable model revision, distance threshold,
Python and package versions, setup time, and Git revision. Source and model
revision changes invalidate index fingerprints: **re-ingest old indexes** after
this PR. Raw passages are resolved from the validated local corpus, not DB text.
Citation checks are not claim entailment or clinical correctness scoring.

## Reproduce

Use Python 3.11+ and a fresh environment. From the repository root:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements-mcp.txt -r backend/requirements-rag.txt
PYTHONPATH=backend python -m pytest backend/tests -q
PYTHONPATH=backend python -m app.evaluation --mode no-index --output work/no-index.json
PYTHONPATH=backend TOKENIZERS_PARALLELISM=false python -m app.evaluation \
  --mode semantic --db work/new-evaluation-index --output work/semantic.json
```

The semantic index directory must not already exist; each run gets a clean index.
Model weights are public and pinned to revision
`e8f8c211226b894fcb81acc59f3b34ba3efd5f42`. Initial download needs internet;
subsequent runs can reuse the Hugging Face cache. No API key is required.
`benchmarks/environment-macos-py312.txt` records the exact local validation
environment; it is an observed macOS/Python 3.12 environment, not a cross-platform
lock. Existing bounded requirement ranges allow different resolver results on CI;
compare report package versions before interpreting numeric drift. Timing is
hardware-dependent and not a production SLA. Reproducibility means fixed inputs,
model revision, metric definitions and a recorded environment, not identical timing.

The missing-index diagnostic calls the real unconfigured evidence-tool path and
must show zero operational availability, not a perfect abstention score. Mock
adapters are used only in unit tests to check hand-calculated metric arithmetic,
forged citations, malformed results, exceptions and infrastructure failures.

## CI and release interpretation

The existing Python 3.11/3.13 job runs evaluator unit regressions and the rest of
the backend tests without a model download. The PR/manual semantic-smoke job runs
the real embedding/MCP/harness integrations and all 22 benchmark queries on a new
index, uploading `stage4a-semantic-evaluation`. Infrastructure errors fail the job;
imperfect quality is reported openly, not converted into a false green quality
claim. There are no calibrated release quality thresholds yet. A green CI means
framework and integrations work, not that deployment for clinical use is safe.

The stored report in `frontend/evaluation-report.json` is a real local semantic
run, not a canned ideal response. The workbench labels its mode and stored timing.
The source revision is the baseline commit plus the Stage 4A working tree; the PR
diff identifies evaluator code. CI artifacts identify the exact PR commit.

## Initial measured results — 31 October 2026

Local Python 3.12/macOS run: recall@3 0.70 (7/10), MRR@3 0.70, citation
provenance precision 1.00 (10/10 citations), citation relevance precision 0.70,
correct abstention 0.75 (9/12), and operational availability 1.00. English
recall is 0.80 and Japanese recall 0.60; English abstention is 5/6 and Japanese
4/6. These small counts do not support a population-level language comparison.
Search p50 was 11.829 ms and p95 13.691 ms with cached model files; index/model
setup took 6558.576 ms and is reported separately. Cold internet download time
is not included.

Both languages missed the MHLW postmarketing question; the Japanese family-report
question also missed. The retriever returned related evidence for both causal
premise questions and the Japanese current-day count question, failing the
expected-abstention labels. There is no synthesis, so this does not mean it
asserted those false premises. Thresholds were not relaxed to hide failures.

Validation: 67 normal tests passed with 3 opt-in integrations skipped; a separate
real-model run passed all 3 semantic/MCP/harness integrations. Browser checks
covered bilingual source switching, report rendering, case filtering, build
journal navigation, and real backend missing-index behavior. The static preview
has no live query capability. PR CI results are recorded separately on GitHub.

## Evaluation scoring integrity follow-up — 31 October 2026

Report schema 2 uses scoring version `trusted-citation-slots-v2`. The original
scorer let a forged passage with a real gold document ID earn recall and MRR
credit. Recall now requires the citation to pass the existing corpus provenance
check. MRR uses the first valid gold citation's original slot, so an invalid or
duplicate citation cannot promote a later valid result to an earlier rank.
Coverage still records whether anything was returned and does not imply validity.
`retrieved_ids` remains a raw diagnostic; `trusted_retrieved_ids` exposes the
validated IDs used for recall. The evaluator source digest identifies the exact
scoring implementation even when a local report was made before committing it.
Schema-1 scores used ID-only recall and deduplicated rank; compare scoring
versions before interpreting historical differences. The workbench's older
stored report remains a historical schema-1 snapshot.

The unchanged 22-case development set rerun on macOS/Python 3.13 produced:
recall@3 7/10, MRR@3 0.70, provenance precision 10/10, relevance precision 7/10,
correct abstention 9/12, operational availability 22/22. English recall was 4/5,
Japanese recall 3/5; English abstention 5/6 and Japanese abstention 4/6. Outcomes
match the original report; the scoring correction does not improve retrieval.
The model revision, benchmark labels and distance threshold were not changed.

Local full-suite validation with model integration enabled: 78 passed, none
skipped. Added regressions cover forged URLs/digests/passages/publishers/sections/
chunks, valid results beyond k, and duplicate/invalid citation rank handling.
The existing PR CI also reruns the real benchmark and preserves its report.
These are author-labelled development cases, not held-out or clinically reviewed
examples. The three false abstentions and three unsupported-query retrievals
remain unresolved; this change fixes measurement integrity, not those failures.
