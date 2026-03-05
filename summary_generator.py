"""Auto-generate SUMMARY.md from ingested sources."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def generate_summary(kb_dir: Path, output_path: Path | None = None) -> str:
    """Generate SUMMARY.md content from local sources. Optionally write to file."""
    sources = kb_dir / "sources"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"# PISTRIK Knowledge Base Summary", "", f"**Last updated**: {now}", ""]

    # Count sources
    source_counts = _count_sources(sources)
    counts_str = ", ".join(f"{v} {k}" for k, v in source_counts.items() if v > 0)
    lines.append(f"**Sources**: {counts_str}")
    lines.append("")

    # API Overview
    api_section = _api_overview(sources / "openapi" / "openapi.json")
    if api_section:
        lines.extend(api_section)

    # Notes summary
    notes_section = _notes_summary(sources / "notes")
    if notes_section:
        lines.extend(notes_section)

    # Web docs summary
    web_section = _web_docs_summary(sources / "web-docs")
    if web_section:
        lines.extend(web_section)

    # Tools reference
    lines.extend([
        "## Available MCP Tools", "",
        "- `search_pistrik(query, top_k)` - semantic search across all PISTRIK knowledge",
        "- `pistrik_endpoint(keyword)` - precise API endpoint lookup",
        "- `pistrik_update()` - re-fetch sources and rebuild knowledge base",
        "",
    ])

    md = "\n".join(lines)

    if output_path:
        output_path.write_text(md, encoding="utf-8")

    return md


def _count_sources(sources: Path) -> dict:
    counts = {}
    web_dir = sources / "web-docs"
    att_dir = web_dir / "attachments"
    counts["web pages"] = sum(1 for f in web_dir.glob("*.md")) if web_dir.exists() else 0
    counts["attachments"] = sum(1 for f in att_dir.iterdir() if f.is_file()) if att_dir.exists() else 0
    counts["notes"] = (
        sum(1 for f in (sources / "notes").iterdir() if f.is_file() and f.name != ".gitkeep")
        if (sources / "notes").exists()
        else 0
    )
    openapi = sources / "openapi" / "openapi.json"
    counts["OpenAPI specs"] = 1 if openapi.exists() else 0
    github_dir = sources / "github-api-docs"
    counts["GitHub API files"] = (
        sum(1 for f in github_dir.glob("*.json"))
        if github_dir.exists()
        else 0
    )
    return counts


def _api_overview(openapi_path: Path) -> list[str]:
    if not openapi_path.exists():
        return []
    spec = json.loads(openapi_path.read_text())
    info = spec.get("info", {})
    paths = spec.get("paths", {})

    endpoint_count = sum(
        len([m for m in methods if not m.startswith("x-") and m != "parameters"])
        for methods in paths.values()
    )

    tag_counter = Counter()
    for methods in paths.values():
        for method, details in methods.items():
            if method.startswith("x-") or method == "parameters":
                continue
            for tag in details.get("tags", ["untagged"]):
                tag_counter[tag] += 1

    lines = [
        "## API Overview", "",
        f"- **Title**: {info.get('title', 'N/A')}",
        f"- **Version**: {info.get('version', 'N/A')}",
        f"- **Endpoints**: {endpoint_count} across {len(tag_counter)} tag groups",
        f"- **Tags**: {', '.join(f'{t} ({c})' for t, c in tag_counter.most_common(10))}",
        "",
    ]
    return lines


def _notes_summary(notes_dir: Path) -> list[str]:
    if not notes_dir.exists():
        return []
    note_files = [f for f in sorted(notes_dir.iterdir()) if f.is_file() and f.name != ".gitkeep"]
    if not note_files:
        return []
    lines = ["## Notes", ""]
    for f in note_files[:10]:
        first_line = f.read_text(encoding="utf-8").strip().split("\n")[0]
        first_line = first_line.lstrip("# ").strip()
        lines.append(f"- `{f.name}`: {first_line[:80]}")
    if len(note_files) > 10:
        lines.append(f"- ... and {len(note_files) - 10} more")
    lines.append("")
    return lines


def _web_docs_summary(web_dir: Path) -> list[str]:
    if not web_dir.exists():
        return []
    md_files = sorted(web_dir.glob("*.md"))
    if not md_files:
        return []
    lines = ["## Web Documentation", ""]
    for f in md_files[:5]:
        lines.append(f"- `{f.name}`")
    att_dir = web_dir / "attachments"
    if att_dir.exists():
        atts = [f.name for f in att_dir.iterdir() if f.is_file()]
        if atts:
            lines.append(f"- Attachments: {', '.join(atts[:10])}")
    lines.append("")
    return lines
