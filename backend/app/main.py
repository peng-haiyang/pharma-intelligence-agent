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

# Stage 2C is isolated from the legacy, unverified keyword baseline.
import logging
import os
from app.verified_rag import retrieve_verified

logger = logging.getLogger(__name__)

@app.post('/api/v2/questions')
def ask_verified(payload: Question):
    db = os.getenv('PHARMA_VERIFIED_DB')
    result = {'question': payload.question, 'answer': None, 'citations': [],
              'status': 'insufficient_evidence', 'synthesis': 'disabled'}
    if not db:
        return {**result, 'reason': 'semantic_index_not_configured'}
    try:
        hits = retrieve_verified(payload.question, db)
    except Exception:
        logger.exception('Verified retrieval unavailable')
        return {**result, 'reason': 'semantic_index_unavailable'}
    if not hits:
        return {**result, 'reason': 'no_evidence_within_distance_threshold'}
    return {**result, 'status': 'retrieved', 'citations': hits,
            'reason': 'Evidence only; relevance and completeness require review. No answer synthesis.'}

# A separate development workbench. Build with scripts/build_demo.py first.
# Same-origin mode can call v2; static hosts remain explicitly offline.
from pathlib import Path
from fastapi.staticfiles import StaticFiles
_demo = Path(__file__).resolve().parents[2] / 'dist'
if _demo.is_dir():
    app.mount('/demo', StaticFiles(directory=_demo, html=True), name='development-demo')
