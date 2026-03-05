import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture
def kb_dir(tmp_path):
    """Set up a minimal pistrik-kb directory structure."""
    sources = tmp_path / "sources"
    (sources / "web-docs" / "attachments").mkdir(parents=True)
    (sources / "openapi").mkdir(parents=True)
    (sources / "github-api-docs").mkdir(parents=True)
    (sources / "notes").mkdir(parents=True)
    return tmp_path


def test_ingest_local_notes(kb_dir):
    from ingest import ingest_local_sources
    from vectorstore import VectorStore

    notes_dir = kb_dir / "sources" / "notes"
    (notes_dir / "meeting.md").write_text("# Meeting\n\nPISTRIK API v2 discussed.")

    store = VectorStore(persist_dir=kb_dir / "chroma_db")
    count = ingest_local_sources(kb_dir, store)
    assert count > 0
    results = store.search("PISTRIK API", top_k=1)
    assert len(results) == 1


def test_ingest_openapi_from_file(kb_dir):
    from ingest import ingest_local_sources
    from vectorstore import VectorStore

    spec = {
        "openapi": "3.0.0",
        "paths": {
            "/api/v1/wastenote": {
                "get": {"summary": "List wastenotes", "operationId": "list", "tags": ["wastenote"]},
            }
        },
    }
    (kb_dir / "sources" / "openapi" / "openapi.json").write_text(json.dumps(spec))

    store = VectorStore(persist_dir=kb_dir / "chroma_db")
    count = ingest_local_sources(kb_dir, store)
    assert count > 0


def test_generate_report():
    from ingest import generate_report

    report = generate_report(
        web_docs={"downloaded": ["a.pdf"], "unsupported_formats": [".xlsx"]},
        openapi_endpoints=5,
        github_files=["collection.json"],
        local_chunks=3,
        total_chunks=20,
    )
    assert "a.pdf" in report
    assert ".xlsx" in report
    assert "5" in report
