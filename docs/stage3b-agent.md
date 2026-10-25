# Stage 3B — bounded evidence orchestration

Stage 3A PR #4 merged as `a81131873f0bf9bed1c2fd112897d220cbf6357a`.
Its head `c873f7d` passed Python CI run 40194420535 on Python 3.11 and 3.13;
the optional semantic-smoke job was skipped. No merge-commit workflow run was
returned by GitHub when inspected. Those checks did not test the MCP protocol.

## Run

From `backend/`:

```bash
pip install -r requirements-mcp.txt
python -m app.agent_cli 'What does PMDA publish?'
python -m pytest -q
```

MCP dependencies now install without the large optional semantic stack. For
successful semantic search, also install `requirements-rag.txt`, ingest the
Stage 2C corpus and set `PHARMA_VERIFIED_DB` (see `stage2c.md`). With no index
configuration, investigation returns `abstained` with an explicit reason.

The CLI emits a JSON report with run ID, status, evidence, documents, limits and
trace. Reports are returned to the caller, not automatically written to disk.
Callers must treat reports containing evidence as potentially sensitive.

## Reuse

`app.agent_harness` exposes `Tool`, `ToolRegistry`, `Limits`, `Run` and
`investigate`. Register trusted module-level Python callables explicitly, with
allowed and required argument names, then call `Run.call(name, arguments)`.
Unregistered tools, extra/missing argument names, non-JSON inputs and inputs
over 8 KiB are rejected. Domain types/bounds are validated by each tool.

A run defaults to four attempted calls, 30 seconds total execution allowance,
15 seconds per worker and 256,000 bytes per serialized result. Configurable
limits have hard upper bounds. Failed/invalid attempts consume the call budget;
repeated requests beyond the budget do not grow the trace. Each worker uses
Python's spawn context and is terminated and joined after timeout, with a kill
fallback. Cleanup may add up to two seconds beyond the execution deadline.
Use a normal importable module and a `__main__` guard when launching callers.

`investigate` is a fixed workflow: search once, then fetch each distinct cited
document. It does not plan from retrieved text, retry, execute evidence as code,
or generate answers. Results are `complete`, `partial`, `abstained` or `failed`.
A completed workflow means evidence was retrieved and documents fetched, not
that any medical or commercial claim has been independently proven.

Errors contain stable codes rather than exception text. Traces include tool
name, step, elapsed time, outcome and returned status, without arguments,
passages or exception messages. Tool-specific abstentions remain visible in
the result. Run instances are sequential and single-use, not thread-safe.

## Verified and unverified coverage

The real MCP SDK test launches `python -m app.mcp_server` as a subprocess,
performs initialization and tool listing, calls both tools, and checks:

- Search without index configuration returns explicit unavailability.
- Document lookup returns real hash-validated JRS corpus metadata and passages.
- Unknown document and invalid search limit paths return structured results.

Harness tests cover real document lookup and no-index abstention through worker
processes, plus deterministic fixture handlers for successful orchestration,
deduplication, partial results, malformed results, exceptions, serialization,
argument/result size bounds, unknown tools, call limits, run/tool timeouts and
worker cleanup. Fixture search success does not prove semantic retrieval.

CI installs the MCP SDK on Python 3.11 and 3.13 and runs the full suite, including
the stdio test. An import check prevents accidentally skipping protocol coverage
if the SDK is missing. The model-backed integration uses the
semantic-smoke job, now run on pull requests and workflow_dispatch. It covers
real model/index retrieval over MCP and through the harness; see
[semantic MCP verification](semantic-mcp-verification.md) for commands and
limits on what those tests establish. The original Stage 3B PR did not validate
successful model-backed MCP search.

The process boundary enforces timeouts for trusted handlers, not security,
network, filesystem or memory isolation. Handlers must not launch descendant
processes. Serialization byte checks bound returned payloads, not peak worker
memory. No LLM planner, remote MCP adapter, deployment, medical correctness
evaluation or live publisher refresh is included.
