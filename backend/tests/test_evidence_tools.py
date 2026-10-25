from app import evidence_tools as tools

def test_search_requires_config(monkeypatch):
    monkeypatch.delenv("PHARMA_VERIFIED_DB", raising=False)
    result = tools.search_evidence("What is the PMDA patient reporting process?")
    assert result["status"] == "unavailable"
    assert result["citations"] == []

def test_search_invalid_input(monkeypatch):
    monkeypatch.setenv("PHARMA_VERIFIED_DB", "dummy")
    assert tools.search_evidence("hi")["status"] == "invalid_request"
    assert tools.search_evidence("A valid question", 0)["status"] == "invalid_request"
    assert tools.search_evidence("A valid question", True)["status"] == "invalid_request"

def test_search_evidence(monkeypatch):
    monkeypatch.setenv("PHARMA_VERIFIED_DB", "dummy")
    monkeypatch.setattr(tools, "retrieve_verified",
                        lambda question, db, limit: [{"id": "pmda", "passage": "Reviewed passage"}])
    result = tools.search_evidence("What does PMDA publish?", limit=2)
    assert result["status"] == "retrieved"
    assert result["citations"][0]["id"] == "pmda"

def test_search_failure_does_not_leak(monkeypatch):
    monkeypatch.setenv("PHARMA_VERIFIED_DB", "dummy")
    def broken(*args, **kwargs):
        raise RuntimeError("secret file path")
    monkeypatch.setattr(tools, "retrieve_verified", broken)
    result = tools.search_evidence("What does PMDA publish?")
    assert result["status"] == "unavailable"
    assert "secret" not in str(result)

def test_document_lookup():
    from app.verified_rag import load_corpus
    doc_id = load_corpus()[0]["id"]
    result = tools.get_evidence_document(doc_id)
    assert result["status"] == "found"
    assert result["document"]["id"] == doc_id
    assert result["passages"]
    assert tools.get_evidence_document("not-a-real-id")["status"] == "not_found"

def test_mcp_module_import_without_optional_dependency():
    from app.mcp_server import build_server
    assert callable(build_server)
