from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Japan Pharma Intelligence Agent", version="0.1.0")

class Question(BaseModel):
    question: str = Field(min_length=5, max_length=2000)

@app.get('/health')
def health():
    return {'status': 'ok', 'version': '0.1.0'}

@app.post('/api/v1/questions')
def ask(payload: Question):
    # Stage 1: no fabricated answers; Stage 2 will connect retrieval.
    return {'status': 'not_ready', 'answer': None, 'citations': [],
            'message': 'Evidence retrieval is not configured yet.',
            'question': payload.question}
