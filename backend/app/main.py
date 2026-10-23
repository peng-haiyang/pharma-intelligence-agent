from fastapi import FastAPI
from pydantic import BaseModel, Field
from app.evidence import retrieve

app = FastAPI(title="Japan Pharma Intelligence Agent", version="0.2.0")

class Question(BaseModel):
    question: str = Field(min_length=5, max_length=2000)

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.2.0"}

@app.post("/api/v1/questions")
def ask(payload: Question):
    matches = retrieve(payload.question)
    if not matches:
        return {"status": "insufficient_evidence", "answer": None,
                "citations": [], "question": payload.question,
                "message": "No matching evidence in the curated public baseline."}
    return {"status": "retrieved", "answer": None, "citations": matches,
            "question": payload.question,
            "message": "Relevant evidence retrieved. LLM synthesis is not enabled; passages are not verified against live source pages."}
