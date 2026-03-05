import pytest
from pathlib import Path


@pytest.fixture
def store(tmp_path):
    from vectorstore import VectorStore

    return VectorStore(persist_dir=tmp_path / "chroma_db")


def test_store_and_search(store):
    chunks = [
        {
            "text": "Wastenote must be created before transport begins",
            "metadata": {"source": "web-docs/page.md", "section": "Rules", "type": "web-doc"},
        },
        {
            "text": "Facility balance tracks incoming and outgoing waste",
            "metadata": {"source": "web-docs/page.md", "section": "Balance", "type": "web-doc"},
        },
    ]
    store.add_chunks(chunks)
    results = store.search("transport document requirements", top_k=1)
    assert len(results) == 1
    assert "transport" in results[0]["text"].lower() or "wastenote" in results[0]["text"].lower()


def test_search_returns_metadata(store):
    chunks = [
        {
            "text": "PISTRIK API uses bearer token authentication",
            "metadata": {"source": "openapi/spec.md", "section": "Auth", "type": "openapi"},
        },
    ]
    store.add_chunks(chunks)
    results = store.search("authentication", top_k=1)
    assert results[0]["metadata"]["type"] == "openapi"
    assert "score" in results[0]


def test_clear_and_rebuild(store):
    chunks = [{"text": "Old data", "metadata": {"source": "old.md", "type": "note"}}]
    store.add_chunks(chunks)
    assert store.count() == 1

    store.clear()
    assert store.count() == 0

    new_chunks = [{"text": "New data", "metadata": {"source": "new.md", "type": "note"}}]
    store.add_chunks(new_chunks)
    assert store.count() == 1


def test_empty_search(store):
    results = store.search("anything", top_k=5)
    assert results == []
