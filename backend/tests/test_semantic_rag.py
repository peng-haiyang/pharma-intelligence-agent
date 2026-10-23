from pathlib import Path
from app.semantic_rag import chunk_text, read_documents

def test_chunk_overlap_and_coverage():
    text = "a" * 1100
    chunks = chunk_text(text, 900, 150)
    assert len(chunks) == 2
    assert chunks[0][-150:] == chunks[1][:150]
    assert len(chunks[1]) == 350

def test_empty_document():
    assert chunk_text("  \n ") == []

def test_invalid_overlap():
    import pytest
    with pytest.raises(ValueError):
        chunk_text("hello", 10, 10)

def test_local_document_ingestion(tmp_path: Path):
    (tmp_path / "source.md").write_text("COPD guideline evidence.", encoding="utf-8")
    (tmp_path / "skip.csv").write_text("not approved", encoding="utf-8")
    docs = read_documents(tmp_path)
    assert len(docs) == 1
    assert docs[0]["source"] == "source.md"
    assert "COPD" in docs[0]["text"]
