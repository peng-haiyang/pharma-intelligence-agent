# Stage 2: Japan evidence retrieval

This PR adds a transparent retrieval baseline to the existing FastAPI API.

## Run
From `backend/`:
```bash
pip install -r requirements.txt
python -m pytest -v
uvicorn app.main:app --reload
```

POST `http://127.0.0.1:8000/api/v1/questions`:
```json
{"question":"What changed in Japan COPD guidelines?"}
```

## Current scope and limitations
- Four short **manually curated summaries** based on the recovered Japan dashboard; **not original ingested source documents**.
- Publisher home-page URLs are **discovery pointers, not claim-level direct citations**.
- Retrieval is term-frequency matching, **not semantic embeddings**.
- No LLM synthesis is performed; the API returns evidence passages and an explicit `answer: null`.
- No live freshness, access control, medical validation, or production monitoring.
- No confidential company or patient information should be submitted.

## Next milestones
1. Replace summaries with retrieved, licensed/approved source documents and direct document URLs.
2. Add document ingestion, chunking, metadata, source dates and provenance.
3. Add embeddings, a vector store and retrieval evaluation against a labelled query set.
4. Add grounded LLM synthesis with claim-level citations and abstention tests.
