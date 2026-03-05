import json
from pathlib import Path


def test_generate_summary_from_openapi(tmp_path):
    from summary_generator import generate_summary

    sources = tmp_path / "sources"
    (sources / "openapi").mkdir(parents=True)
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "PISTRIK API", "version": "1.0"},
        "paths": {
            "/api/v1/wastenote": {"get": {"tags": ["wastenote"]}, "post": {"tags": ["wastenote"]}},
            "/api/v1/facility": {"get": {"tags": ["registry"]}},
        },
    }
    (sources / "openapi" / "openapi.json").write_text(json.dumps(spec))

    md = generate_summary(tmp_path)
    assert "PISTRIK" in md
    assert "3 endpoints" in md or "3" in md
    assert "wastenote" in md.lower()


def test_generate_summary_includes_notes(tmp_path):
    from summary_generator import generate_summary

    sources = tmp_path / "sources"
    (sources / "notes").mkdir(parents=True)
    (sources / "openapi").mkdir(parents=True)
    (sources / "notes" / "issue.md").write_text("# Known Issue\n\nHP codes required at confirmation.")

    md = generate_summary(tmp_path)
    assert "Known" in md or "Notes" in md


def test_generate_summary_writes_file(tmp_path):
    from summary_generator import generate_summary

    sources = tmp_path / "sources"
    (sources / "openapi").mkdir(parents=True)

    generate_summary(tmp_path, output_path=tmp_path / "SUMMARY.md")
    assert (tmp_path / "SUMMARY.md").exists()
    content = (tmp_path / "SUMMARY.md").read_text()
    assert "PISTRIK Knowledge Base Summary" in content


def test_summary_under_150_lines(tmp_path):
    from summary_generator import generate_summary

    sources = tmp_path / "sources"
    (sources / "openapi").mkdir(parents=True)
    # Big spec
    paths = {}
    for i in range(50):
        paths[f"/api/v1/resource{i}"] = {"get": {"tags": [f"tag{i % 5}"]}}
    spec = {"openapi": "3.0.0", "info": {"title": "PISTRIK", "version": "1.0"}, "paths": paths}
    (sources / "openapi" / "openapi.json").write_text(json.dumps(spec))

    md = generate_summary(tmp_path)
    assert md.count("\n") < 150
