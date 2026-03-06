import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_fetch_openapi(tmp_path):
    from fetchers import fetch_openapi

    fake_spec = {"openapi": "3.0.0", "paths": {"/api/v1/test": {}}}
    with patch("fetchers.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: fake_spec, raise_for_status=lambda: None
        )
        result = fetch_openapi(dest_dir=tmp_path)

    assert (tmp_path / "openapi.json").exists()
    saved = json.loads((tmp_path / "openapi.json").read_text())
    assert saved["openapi"] == "3.0.0"
    assert result == fake_spec


def test_fetch_web_docs_discovers_links(tmp_path):
    from fetchers import fetch_web_docs

    html = """
    <html><body>
        <a href="/file.pdf">PDF doc</a>
        <a href="/file.docx">Word doc</a>
        <a href="/file.xlsx">Excel doc</a>
        <p>Page content here</p>
    </body></html>
    """
    with patch("fetchers.requests.get") as mock_get:
        response = MagicMock(status_code=200, text=html, content=html.encode(), raise_for_status=lambda: None)
        mock_get.return_value = response
        result = fetch_web_docs(dest_dir=tmp_path, urls={"test": "https://example.com"})

    assert "unsupported_formats" in result
    assert ".xlsx" in result["unsupported_formats"]


def test_fetch_github_api_docs(tmp_path):
    from fetchers import fetch_github_api_docs

    fake_tree = {"tree": [{"path": "PISTRIK-collection.json", "type": "blob"}]}
    fake_collection = {"info": {"name": "PISTRIK API"}, "item": []}

    def mock_get_side_effect(url, **kwargs):
        resp = MagicMock(status_code=200, raise_for_status=lambda: None)
        if "git/trees" in url:
            resp.json = lambda: fake_tree
        else:
            resp.json = lambda: fake_collection
            resp.text = json.dumps(fake_collection)
        return resp

    with patch("fetchers.requests.get", side_effect=mock_get_side_effect):
        result = fetch_github_api_docs(dest_dir=tmp_path)

    assert len(result) >= 1


def test_discover_file_formats():
    from fetchers import discover_file_formats

    links = ["/a.pdf", "/b.docx", "/c.xlsx", "/d.pptx", "/e.pdf", "/page"]
    supported, unsupported = discover_file_formats(links)
    assert ".pdf" in supported
    assert ".docx" in supported
    assert ".xlsx" in unsupported
    assert ".pptx" in unsupported
