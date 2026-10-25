# Real semantic MCP verification

Stage 3B PR #5 merged at `74d35f4a9ffc0101fd1fdfdb1f34c3d32fdfd851`.
Its PR CI passed on Python 3.11 and 3.13. That CI tested actual stdio transport
and document lookup, but search used the no-index abstention path.

This follow-up adds real embedding-model integration coverage and fixes cosine
distance roundoff handling. The configured model and upper retrieval threshold
are unchanged; answer synthesis remains disabled.

The first real MCP run returned insufficient evidence for exact MHLW and JRS
passages. Raw Chroma results were `-2.384185791015625e-7` for identical vectors,
which the strict nonnegative distance check discarded. Values in `[-1e-6, 0)`
are now normalized to zero. Values below that range, non-finite distances,
untrusted IDs and distances above the upper threshold remain rejected. Unit
regressions test both edges of the numerical tolerance and the 0.35 threshold.

## Reproduce

From `backend/`, in a virtual environment:

```bash
pip install -r requirements-mcp.txt -r requirements-rag.txt
RUN_SEMANTIC_INTEGRATION=1 TOKENIZERS_PARALLELISM=false python -m pytest \
  tests/test_verified_integration.py tests/test_semantic_mcp_integration.py -v
```

The first run downloads the public `paraphrase-multilingual-MiniLM-L12-v2`
model. Set `HF_HOME` to a writable cache location if needed. Tests create an
isolated temporary persistent Chroma index from the three hash-validated corpus
entries; they do not use or modify a pre-existing user index.

The new MCP integration test starts the real server through the MCP SDK stdio
client, initializes the session, lists both tools, searches for each corpus
passage with `limit=1`, then fetches the cited document. It asserts the expected
ID, corpus passage, publisher URL, SHA-256 and default distance gate (0.35),
plus agreement between search and fetched-document provenance.

A separate test runs `investigate` against the same real index and asserts
successful search, document hydration and both trace events. It explicitly uses
a 180-second run budget and 120-second tool budget to allow model loading in a
new worker. This does not establish that a cold model fits the default
15-second tool budget; applications must measure and configure that allowance.

## CI and interpretation

The `semantic-smoke` job now runs on pull requests and manual workflow dispatch,
installs both optional dependency sets, and runs the existing semantic roundtrip
plus the new MCP and harness integrations. The normal Python 3.11/3.13 matrix
continues to run without model downloads; these three integration tests skip
there unless explicitly enabled. Model-download or integration errors fail the
semantic job, rather than silently skipping it.

Exact-passage queries test the model/index/protocol plumbing, not retrieval
quality on unseen questions, multilingual relevance, clinical correctness, or
live publisher freshness. The existing roundtrip uses a short COPD query with
an explicit 0.65 distance threshold; the new MCP/harness tests use the production
0.35 default and do not relax it. No external API keys, proprietary information,
LLM generation or autonomous planning are involved.
