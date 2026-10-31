# Stage 4B — live questions and evidence activity

The development Site now runs a self-contained server for free-text English and
Japanese questions. This replaces its static-only question limitation. The original
Japan market Site is untouched and the development Site remains owner-private.

## What happens on a request

`POST /api/demo/investigate` accepts a JSON question, then streams SSE `activity`
events for request acceptance, scope checks, retrieval, source integrity and final
status. Events describe actual operations with sequence numbers and elapsed time;
there are no inserted delays, simulated tools or internal reasoning traces. Fast
checks can arrive in one browser update. The final `result` contains evidence
passages or an explicit abstention. The client can cancel, and treats a truncated
stream or network error as a failure rather than claiming a complete answer.

The question desk accepts custom text (5–2000 characters), provides optional
examples, shows actual source passages and publisher links, and keeps authored
benchmark references collapsed and separate from request results. The sources,
Stage 4A report and build journal remain accessible in their own tabs. All response
text uses text nodes; source links are limited to approved HTTPS publisher hosts.

## Hosting and retrieval choice

The Site runs in a small JavaScript Worker, which cannot run the existing Python
Chroma/embedding stack within its runtime budget. Its engine is explicitly
`snapshot-bm25-v1`: real lexical retrieval over the same three approved bilingual
summaries, with English word matching and Japanese bigram matching. This is not
a semantic model, not the legacy unverified baseline, and not a mock response or
lookup of benchmark gold answers. The live engine imports only approved source
material. Benchmark labels are used only by evaluation; their visibility in the
case inspector does not affect live retrieval.

Before retrieval, conservative exclusion rules abstain for recognized current
counts/prices/forecasts, personal dosing, causal proof and instruction overrides.
These are a narrow demonstration policy, not comprehensive clinical guardrails:
paraphrases can evade rules and benign questions may be rejected. Ranking uses
fixed BM25-style scoring and a minimum overlap gate, with at most three candidates.
Each candidate's full editorial source text is SHA-256 checked against its manifest
digest; its normalized passage and publisher URL are also checked. Integrity
failure yields `unavailable` with no citations. The source review remains the
23 October 2026 snapshot; the server does not fetch current publisher pages.
No LLM answer synthesis or autonomous planner is introduced.

The Stage 4A Python semantic engine and report are unchanged. Local `/demo/` mode
can still use `/api/v2/questions`, with final-result-only behavior clearly labelled.
A future hosted semantic service needs a separate suitable Python/model host; it
must not be claimed as deployed by this Worker feature.

## Data and resource boundaries

Requests are same-origin, JSON-only and bounded to 8192 bytes before parsing.
Only a single `question` field is accepted. This server does not persist questions,
responses or activity; the browser holds the current run only. There are no external
model calls, database writes, browser API keys or app-level raw-question logs.
Normal hosting infrastructure may retain request metadata; this is not a claim
about provider retention. Access remains behind the existing owner-private Site
sign-in gate, and the endpoint returns `no-store` with a restrictive CSP. Work is
bounded to three small summaries. No distributed rate limit is claimed; do not
expand the audience without adding suitable abuse/resource controls.

## Reproduce and evaluate

From repository root with Python 3.11+ and Node 22+:

```bash
python scripts/build_hosted.py
node --test hosted/tests/*.test.mjs
python scripts/evaluate_hosted.py
node scripts/serve_hosted.mjs
```

Open `http://127.0.0.1:8766/`. The server runs the exact bundled Worker using an
HTTP adapter; it is not a separate implementation of the endpoint. No npm install,
model download or secret is required. `scripts/build_hosted.py` first invokes the
existing manifest-gated corpus builder, then embeds assets and the validated
summaries into `dist-hosted/server/index.js`. Build output is ignored by Git.

The hosted evaluation runs the actual engine on all 22 Stage 4A cases, then reuses
the Python metric definitions. Stored results are in
`benchmarks/hosted-lexical-report.json`. Initial development results: recall@3 0.90,
MRR@3 0.90, provenance precision 1.00, citation relevance precision about 0.69,
correct abstention 1.00, operational rate 1.00. Extra irrelevant citations lower
citation relevance despite correct top-ranked evidence. These visible development
cases informed policy design, so the numbers are not held-out validation and do
not establish superiority over semantic retrieval. In-process latency excludes
HTTP transport and Worker startup; it is not a hosted-response SLA.

The hosted CI job runs meaningful engine/stream/validation/integrity/cancellation
regressions, checks the UI script, builds the Worker and publishes the report plus
bundle as a downloadable artifact. Existing Python/MCP CI remains separate.
The next evidence-quality milestone still requires independent bilingual domain
review and approved broader sources; this feature does not manufacture that review.

## Publish the existing development Site

Use the existing Site project identity and source repository, preserving its
owner-private audience. Remove the source manifest's `static` setting only after
preparing the Worker; copy the bundle into the source checkout's `worker/index.js`
and use the Worker ESM build/validation scripts to emit `dist/server/index.js` and
`dist/.openai/hosting.json`. Save and deploy the matching pushed source archive.
Keep the preceding static Site version for rollback. A GitHub merge does not
automatically redeploy this Site. Record the verified Site version in
`docs/development-preview.md` after native deployment succeeds.

## Validation record

Local checks: all 8 hosted-engine/Worker tests passed, all 67 existing Python tests
passed (3 model integrations remain opt-in), JS syntax and diff checks passed,
and the generated ESM artifact passed its export validator. Browser testing used
custom English and Japanese questions, confirmed real source passages and ordered
activity events, checked unsupported-price abstention, and verified that the
separate Stage 4A semantic report remains clearly labelled. Hosted deployment
status succeeded; sign-in requirements remain unchanged. CI results are available
on the Stage 4B PR rather than assumed from this local run.
