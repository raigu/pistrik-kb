import json
import pytest
from pathlib import Path


@pytest.fixture
def kb_with_data(tmp_path):
    """Create a minimal KB with some data ingested."""
    from vectorstore import VectorStore
    from chunker import chunk_openapi

    sources = tmp_path / "sources"
    (sources / "openapi").mkdir(parents=True)
    (sources / "notes").mkdir(parents=True)

    spec = {
        "openapi": "3.0.0",
        "info": {"title": "PISTRIK", "version": "1.0"},
        "paths": {
            "/api/v1/wastenote": {
                "get": {"summary": "List wastenotes", "operationId": "listWastenotes", "tags": ["wastenote"]},
                "post": {"summary": "Create wastenote", "operationId": "createWastenote", "tags": ["wastenote"]},
            },
            "/api/v1/facility": {
                "get": {"summary": "List facilities", "operationId": "listFacilities", "tags": ["registry"]},
            },
        },
    }
    (sources / "openapi" / "openapi.json").write_text(json.dumps(spec))

    store = VectorStore(persist_dir=tmp_path / "chroma_db")
    chunks = chunk_openapi(spec)
    chunks.append({
        "text": "Waste confirmation requires all three parties to confirm",
        "metadata": {"source": "notes/rules.md", "section": "Confirmation", "type": "note"},
    })
    store.add_chunks(chunks)

    return tmp_path


def test_handle_search(kb_with_data):
    from mcp_server import handle_search

    results = handle_search("waste confirmation", top_k=2, kb_dir=kb_with_data)
    assert len(results) > 0
    assert "text" in results[0]
    assert "metadata" in results[0]


def test_handle_endpoint_by_keyword(kb_with_data):
    from mcp_server import handle_endpoint

    results = handle_endpoint("wastenote", kb_dir=kb_with_data)
    assert len(results) == 2  # GET and POST
    assert any(r["method"] == "GET" for r in results)
    assert any(r["method"] == "POST" for r in results)


def test_handle_endpoint_by_path(kb_with_data):
    from mcp_server import handle_endpoint

    results = handle_endpoint("/api/v1/facility", kb_dir=kb_with_data)
    assert len(results) == 1
    assert results[0]["path"] == "/api/v1/facility"


def test_handle_endpoint_no_match(kb_with_data):
    from mcp_server import handle_endpoint

    results = handle_endpoint("nonexistent", kb_dir=kb_with_data)
    assert results == []
