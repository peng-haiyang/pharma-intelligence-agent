"""Real SDK client/server stdio exchanges; no mock transport or embedding model."""
import asyncio
import json
import os
import sys
import pytest

pytest.importorskip('mcp')
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_stdio_listing_and_both_tools():
    async def exercise():
        env = dict(os.environ)
        env.pop('PHARMA_VERIFIED_DB', None)
        parameters = StdioServerParameters(command=sys.executable,
            args=['-m', 'app.mcp_server'], env=env)
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listed = await session.list_tools()
                assert {t.name for t in listed.tools} == {
                    'search_verified_evidence', 'get_verified_document'}
                async def call(name, arguments):
                    response = await session.call_tool(name, arguments)
                    assert not response.isError
                    return json.loads(next(c.text for c in response.content if c.type == 'text'))
                search = await call('search_verified_evidence', {'question': 'What does PMDA publish?'})
                assert search['status'] == 'unavailable'
                assert search['reason'] == 'semantic_index_not_configured'
                doc = await call('get_verified_document', {'document_id': 'jrs-copd'})
                assert doc['status'] == 'found'
                assert doc['document']['publisher'] == 'JRS'
                assert doc['passages']
                assert (await call('get_verified_document', {'document_id': 'missing'}))['status'] == 'not_found'
                assert (await call('search_verified_evidence', {'question': 'hello', 'limit': 0}))['status'] == 'invalid_request'
    asyncio.run(asyncio.wait_for(exercise(), timeout=30))
