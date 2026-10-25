"""MCP stdio server. Run: python -m app.mcp_server

Requires optional dependency: pip install -r requirements-mcp.txt
Keep stdout reserved for MCP protocol messages.
"""
from app.evidence_tools import search_evidence, get_evidence_document

def build_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("Install backend/requirements-mcp.txt") from exc

    server = FastMCP("Japan Pharma Verified Evidence")

    @server.tool()
    def search_verified_evidence(question: str, limit: int = 3) -> dict:
        """Search a local verified PMDA/MHLW/JRS evidence index; returns passages and provenance, never generated answers."""
        return search_evidence(question, limit)

    @server.tool()
    def get_verified_document(document_id: str) -> dict:
        """Retrieve provenance metadata and approved passages for a verified document ID."""
        return get_evidence_document(document_id)

    return server

def main():
    build_server().run(transport="stdio")

if __name__ == "__main__":
    main()
