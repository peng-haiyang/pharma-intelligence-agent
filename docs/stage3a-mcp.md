# Stage 3A — Read-only MCP evidence tools

This adds an MCP stdio server around the verified Stage 2C corpus. It does not
crawl PMDA, MHLW or JRS websites, write files, or synthesize medical claims.

## Setup
From `backend/`:

```bash
pip install -r requirements-mcp.txt
pip install -r requirements-rag.txt  # Needed for semantic search/ingestion
# First run Stage 2C verified ingestion to build the local Chroma index.
export PHARMA_VERIFIED_DB=/absolute/path/to/local/verified-chroma
python -m app.mcp_server
```

The server speaks MCP JSON-RPC over **stdio**, so do not type questions directly
into the terminal process. Configure your MCP-capable client to start the command
`python -m app.mcp_server` with its working directory set to `backend/`
and the `PHARMA_VERIFIED_DB` environment variable set.

## Tools

- `search_verified_evidence(question, limit=3)`: returns matching reviewed
  passages, metadata and distance, or an explicit abstention.
- `get_verified_document(document_id)`: returns verified manifest metadata
  and reviewed passages for a specific ID.

## Boundaries

- Both tools are read-only; no network crawling or internal data ingestion.
- All content comes from the local, hash-validated Stage 2C manifest.
- Publisher URLs are provenance pointers, not independent proof of every claim.
- Retrieval similarity is not factual confidence.
- No answer generation, autonomous planning, authentication or deployment.
- Use trusted local clients only; stdio inherits the client's permissions.
- The normal CI job tests tool behavior without downloading embedding models.
- CI now runs real MCP stdio initialization, listing and both tool calls.
  The normal matrix tests search in the no-index abstention path. The separate
  semantic-smoke job tests real model/index search over MCP on pull requests
  and manual dispatch. See [verification](semantic-mcp-verification.md).
