# Stage 2B: local semantic document retrieval

This is an **optional semantic retrieval prototype**. The existing API remains unchanged until integration and evaluation are complete.

## Local setup

From `backend/`:

```bash
pip install -r requirements-rag.txt
mkdir -p ../documents/approved
# Put only approved, public .txt or .md documents in ../documents/approved
python -m scripts.ingest_documents --source ../documents/approved --db ../.chroma
```

Python example:

```python
from app.semantic_rag import semantic_retrieve
hits = semantic_retrieve("What do the COPD guidelines say?", "../.chroma")
print(hits)
```

The first local run may download the multilingual embedding model. Do not run on a restricted machine without reviewing its network and data policies.

## Limitations and safety
- Only manually supplied, approved local text/Markdown documents are ingested.
- Do not upload internal GSK, patient, HCP, personal or commercially confidential data.
- Documents must have verified source URLs, dates and licenses in a future metadata manifest before claims can be cited externally.
- Similarity distance is **not** factual confidence. Retrieval may return irrelevant results; relevance thresholds and abstention need labelled evaluation.
- No LLM answer synthesis, MCP or production authentication yet.
- CI runs deterministic chunking and ingestion-unit tests, not model downloads or full vector-search integration.
- Re-ingesting edited files adds new IDs; versioning/deletion reconciliation is a follow-on task.
