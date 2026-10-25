"""Opt-in real model + persistent Chroma + MCP subprocess + bounded harness.

Exact-passage queries establish plumbing, not held-out retrieval quality.
"""
import asyncio
import json
import os
import sys
from datetime import timedelta

import pytest

from app.agent_harness import Limits, investigate
from app.verified_rag import ingest_verified, load_corpus

pytestmark = pytest.mark.skipif(
    os.getenv('RUN_SEMANTIC_INTEGRATION') != '1',
    reason='Explicit model download opt-in required',
)


@pytest.fixture(scope='module')
def indexed_corpus(tmp_path_factory):
    documents = load_corpus()
    db = str(tmp_path_factory.mktemp('semantic-mcp') / 'chroma')
    assert ingest_verified(db) == len(documents)
    return db, {doc['id']: doc for doc in documents}


def test_semantic_search_and_document_over_stdio(indexed_corpus):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    db, documents = indexed_corpus

    async def exercise():
        parameters = StdioServerParameters(
            command=sys.executable, args=['-m', 'app.mcp_server'],
            env={**os.environ, 'PHARMA_VERIFIED_DB': db},
        )
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=120)) as session:
                await session.initialize()
                assert {tool.name for tool in (await session.list_tools()).tools} == {
                    'search_verified_evidence', 'get_verified_document'}

                async def call(name, arguments):
                    response = await session.call_tool(name, arguments)
                    assert not response.isError
                    return json.loads(next(item.text for item in response.content if item.type == 'text'))

                for doc_id, expected in documents.items():
                    result = await call('search_verified_evidence',
                        {'question': expected['passage'], 'limit': 1})
                    assert result['status'] == 'retrieved', result
                    hit = result['citations'][0]
                    assert hit['id'] == doc_id
                    assert hit['passage'] == expected['passage']
                    assert hit['sha256'] == expected['sha256']
                    assert hit['url'] == expected['url']
                    assert 0 <= hit['distance'] <= 0.35
                    fetched = await call('get_verified_document', {'document_id': hit['id']})
                    assert fetched['status'] == 'found'
                    assert fetched['document']['id'] == doc_id
                    assert fetched['document']['sha256'] == hit['sha256']
                    assert expected['passage'] in [p['passage'] for p in fetched['passages']]

    asyncio.run(asyncio.wait_for(exercise(), timeout=240))


def test_real_index_through_bounded_harness(indexed_corpus, monkeypatch):
    db, documents = indexed_corpus
    monkeypatch.setenv('PHARMA_VERIFIED_DB', db)
    expected = documents['jrs-copd']
    # Explicit cold-start allowance: model import/load happens inside the worker.
    result = investigate(expected['passage'],
        limits=Limits(timeout_seconds=180, tool_timeout_seconds=120))
    assert result['status'] == 'complete', result
    assert result['evidence']['citations'][0]['id'] == 'jrs-copd'
    assert result['documents'][0]['document']['sha256'] == expected['sha256']
    assert [event['tool'] for event in result['trace']] == [
        'search_verified_evidence', 'get_verified_document']
    assert all(event['outcome'] == 'ok' for event in result['trace'])
