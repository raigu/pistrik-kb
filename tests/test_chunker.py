import json
import pytest


def test_chunk_by_headings():
    from chunker import chunk_markdown

    text = """# Title

Intro paragraph.

## Section A

Content for section A. This is important.

## Section B

Content for section B.
"""
    chunks = chunk_markdown(text)
    assert len(chunks) >= 2
    assert any("Section A" in c["text"] for c in chunks)
    assert any("Section B" in c["text"] for c in chunks)
    assert all("section" in c["metadata"] for c in chunks)


def test_chunk_large_section_splits():
    from chunker import chunk_markdown

    # Section with >1000 tokens worth of text (approx 5 words per token)
    long_para = ("This is a test sentence with several words. " * 250)
    text = f"## Big Section\n\n{long_para}"
    chunks = chunk_markdown(text, max_tokens=500)
    assert len(chunks) > 1
    for c in chunks:
        assert c["metadata"]["section"] == "Big Section"


def test_chunk_openapi():
    from chunker import chunk_openapi

    spec = {
        "paths": {
            "/api/v1/wastenote": {
                "get": {
                    "summary": "List wastenotes",
                    "operationId": "listWastenotes",
                    "tags": ["wastenote"],
                    "parameters": [{"name": "status", "in": "query"}],
                },
                "post": {
                    "summary": "Create wastenote",
                    "operationId": "createWastenote",
                    "tags": ["wastenote"],
                    "requestBody": {"content": {"application/json": {}}},
                },
            }
        }
    }
    chunks = chunk_openapi(spec)
    assert len(chunks) == 2
    assert any("GET" in c["text"] for c in chunks)
    assert any("POST" in c["text"] for c in chunks)
    assert all(c["metadata"]["type"] == "openapi" for c in chunks)


def test_chunk_postman():
    from chunker import chunk_postman

    collection = {
        "info": {"name": "PISTRIK API"},
        "item": [
            {
                "name": "List wastenotes",
                "request": {
                    "method": "GET",
                    "url": {"raw": "{{baseUrl}}/api/v1/wastenote"},
                    "header": [{"key": "Authorization", "value": "Bearer {{token}}"}],
                },
            },
            {
                "name": "Create wastenote",
                "request": {
                    "method": "POST",
                    "url": {"raw": "{{baseUrl}}/api/v1/wastenote"},
                    "body": {"mode": "raw", "raw": '{"waste_code": "17 01 01"}'},
                },
            },
        ],
    }
    chunks = chunk_postman(collection)
    assert len(chunks) == 2
    assert all(c["metadata"]["type"] == "postman" for c in chunks)
    assert any("POST" in c["text"] for c in chunks)


def test_chunk_plain_text():
    from chunker import chunk_plain_text

    text = "Short note about a meeting.\n\nPISTRIK API discussion."
    chunks = chunk_plain_text(text, source="notes/meeting.txt")
    assert len(chunks) >= 1
    assert chunks[0]["metadata"]["source"] == "notes/meeting.txt"
