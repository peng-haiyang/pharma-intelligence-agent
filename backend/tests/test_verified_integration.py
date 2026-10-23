import os
import pytest
from app.verified_rag import ingest_verified, retrieve_verified

@pytest.mark.skipif(os.getenv('RUN_SEMANTIC_INTEGRATION') != '1',reason='Explicit model download opt-in required')
def test_real_model_roundtrip(tmp_path):
    db=str(tmp_path/'chroma')
    assert ingest_verified(db)==3
    assert ingest_verified(db)==3
    hits=retrieve_verified('COPD smoking cessation inhaled bronchodilators',db,max_distance=0.65)
    assert hits and hits[0]['id']=='jrs-copd'
