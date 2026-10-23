from fastapi.testclient import TestClient
from app.main import app
from app.evidence import retrieve

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_retrieves_copd_evidence():
    response = client.post("/api/v1/questions", json={"question": "What is the COPD guideline update?"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "retrieved"
    assert any("guideline" in c["title"].lower() for c in body["citations"])
    assert all(c["url"].startswith("https://") for c in body["citations"])
    assert body["answer"] is None

def test_no_evidence_fallback():
    response = client.post("/api/v1/questions", json={"question": "Quantum rocket launch trajectory"})
    assert response.json()["status"] == "insufficient_evidence"
    assert response.json()["citations"] == []

def test_rejects_short_question():
    assert client.post("/api/v1/questions", json={"question": "hi"}).status_code == 422

def test_limit():
    assert len(retrieve("asthma COPD Japan vaccines", limit=2)) <= 2
