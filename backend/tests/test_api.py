from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    assert client.get('/health').json()['status'] == 'ok'

def test_no_ungrounded_answer():
    response = client.post('/api/v1/questions', json={'question': 'What changed in Japan NHI access?'})
    assert response.status_code == 200
    body = response.json()
    assert body['answer'] is None
    assert body['status'] == 'retrieved'
    assert any(item['id'] == 'mhlw-prices' for item in body['citations'])

def test_short_question_rejected():
    assert client.post('/api/v1/questions', json={'question': 'Hi'}).status_code == 422
