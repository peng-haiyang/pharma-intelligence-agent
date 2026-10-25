"""Read-only, framework-independent evidence tools for API and MCP clients."""
import os
import logging
from app.verified_rag import load_corpus, retrieve_verified

logger = logging.getLogger(__name__)

def search_evidence(question: str, limit: int = 3) -> dict:
    if not isinstance(question, str) or not 5 <= len(question.strip()) <= 2000:
        return {"status": "invalid_request", "citations": [], "reason": "invalid_question"}
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 10:
        return {"status": "invalid_request", "citations": [], "reason": "invalid_limit"}
    db = os.getenv("PHARMA_VERIFIED_DB")
    if not db:
        return {"status": "unavailable", "citations": [], "reason": "semantic_index_not_configured"}
    try:
        hits = retrieve_verified(question, db, limit=limit)
    except Exception:
        logger.exception("Evidence search failed")
        return {"status": "unavailable", "citations": [], "reason": "semantic_index_unavailable"}
    if not hits:
        return {"status": "insufficient_evidence", "citations": [],
                "reason": "no_evidence_within_distance_threshold"}
    return {"status": "retrieved", "citations": hits,
            "reason": "Evidence only. No LLM synthesis or claim verification."}

def get_evidence_document(document_id: str) -> dict:
    if not isinstance(document_id, str) or not 1 <= len(document_id) <= 80:
        return {"status": "invalid_request", "reason": "invalid_document_id"}
    try:
        documents = [doc for doc in load_corpus() if doc["id"] == document_id]
    except Exception:
        logger.exception("Evidence corpus unavailable")
        return {"status": "unavailable", "reason": "verified_corpus_unavailable"}
    if not documents:
        return {"status": "not_found", "reason": "unknown_document_id"}
    first = documents[0]
    fields = ("id", "publisher", "title", "url", "section", "language",
              "published", "accessed", "verified", "verification_method",
              "content_kind", "rights", "sha256")
    return {"status": "found", "document": {k: first[k] for k in fields},
            "passages": [{"chunk": doc["chunk"], "passage": doc["passage"]}
                         for doc in documents]}
