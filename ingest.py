#!/usr/bin/env python3
"""Ingestion orchestrator: fetch, parse, chunk, embed, generate summary."""

import json
import logging
import sys
from pathlib import Path

from chunker import chunk_markdown, chunk_openapi, chunk_postman, chunk_plain_text
from fetchers import fetch_openapi, fetch_web_docs, fetch_github_api_docs
from parsers import parse_file, SUPPORTED_EXTENSIONS
from vectorstore import VectorStore

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent


def ingest_local_sources(kb_dir: Path, store: VectorStore) -> int:
    """Ingest all local source files into the vector store. Returns chunk count."""
    all_chunks = []
    sources = kb_dir / "sources"

    # Notes
    notes_dir = sources / "notes"
    if notes_dir.exists():
        for f in sorted(notes_dir.iterdir()):
            if f.suffix.lower() in {".md", ".txt"}:
                text = parse_file(f)
                chunks = chunk_plain_text(text, source=f"notes/{f.name}", doc_type="note")
                all_chunks.extend(chunks)
                logger.info(f"Notes: {f.name} -> {len(chunks)} chunks")

    # Web docs (already fetched to local)
    web_dir = sources / "web-docs"
    if web_dir.exists():
        for f in sorted(web_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in {".md", ".txt"}:
                text = parse_file(f)
                chunks = chunk_markdown(text, source=f"web-docs/{f.name}", doc_type="web-doc")
                all_chunks.extend(chunks)
                logger.info(f"Web doc: {f.name} -> {len(chunks)} chunks")

    # Web doc attachments (PDF, DOCX)
    att_dir = sources / "web-docs" / "attachments"
    if att_dir.exists():
        for f in sorted(att_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                try:
                    text = parse_file(f)
                    chunks = chunk_markdown(
                        text, source=f"web-docs/attachments/{f.name}", doc_type=f.suffix.lstrip(".")
                    )
                    all_chunks.extend(chunks)
                    logger.info(f"Attachment: {f.name} -> {len(chunks)} chunks")
                except ValueError:
                    logger.warning(f"Skipping unsupported: {f.name}")

    # OpenAPI
    openapi_file = sources / "openapi" / "openapi.json"
    if openapi_file.exists():
        spec = json.loads(openapi_file.read_text())
        chunks = chunk_openapi(spec)
        all_chunks.extend(chunks)
        logger.info(f"OpenAPI: {len(chunks)} endpoint chunks")

    # GitHub API docs (Postman collections)
    github_dir = sources / "github-api-docs"
    if github_dir.exists():
        for f in sorted(github_dir.iterdir()):
            if f.suffix == ".json" and "collection" in f.name.lower():
                collection = json.loads(f.read_text())
                chunks = chunk_postman(collection, source=f"github-api-docs/{f.name}")
                all_chunks.extend(chunks)
                logger.info(f"Postman: {f.name} -> {len(chunks)} chunks")
            elif f.suffix == ".json" and "environment" in f.name.lower():
                # Environment files stored as single reference chunk
                text = f"Postman Environment: {f.name}\n{f.read_text()}"
                all_chunks.append({
                    "text": text,
                    "metadata": {"source": f"github-api-docs/{f.name}", "section": "", "type": "postman-env"},
                })

    # Store all chunks
    if all_chunks:
        store.clear()
        store.add_chunks(all_chunks)
        logger.info(f"Total: {len(all_chunks)} chunks embedded")

    return len(all_chunks)


def generate_report(
    web_docs: dict | None = None,
    openapi_endpoints: int = 0,
    github_files: list[str] | None = None,
    local_chunks: int = 0,
    total_chunks: int = 0,
) -> str:
    """Generate human-readable ingestion report."""
    lines = ["# Ingestion Report", ""]

    if web_docs:
        lines.append(f"## Web Docs")
        lines.append(f"- Page saved: {web_docs.get('page_saved', 'N/A')}")
        lines.append(f"- Downloads: {', '.join(web_docs.get('downloaded', [])) or 'none'}")
        unsupported = web_docs.get("unsupported_formats", [])
        if unsupported:
            lines.append(f"")
            lines.append(f"**WARNING: Unsupported formats found on page:** {', '.join(unsupported)}")
            lines.append(f"To add support, install the relevant Python package and update parsers.py")

    lines.append(f"")
    lines.append(f"## Stats")
    lines.append(f"- OpenAPI endpoints: {openapi_endpoints}")
    lines.append(f"- GitHub files: {', '.join(github_files or [])}")
    lines.append(f"- Total chunks: {total_chunks}")

    return "\n".join(lines)


def run_full_ingestion(kb_dir: Path | None = None) -> str:
    """Full pipeline: fetch remote sources, then ingest everything."""
    kb_dir = kb_dir or ROOT
    sources = kb_dir / "sources"

    # 1. Fetch remote sources
    logger.info("Fetching OpenAPI spec...")
    try:
        spec = fetch_openapi(dest_dir=sources / "openapi")
        openapi_endpoints = len(spec.get("paths", {}))
    except Exception as e:
        logger.warning(f"OpenAPI fetch failed: {e}")
        spec = {}
        openapi_endpoints = 0

    logger.info("Fetching web docs...")
    try:
        web_report = fetch_web_docs(dest_dir=sources / "web-docs")
    except Exception as e:
        logger.warning(f"Web docs fetch failed: {e}")
        web_report = None

    logger.info("Fetching GitHub API docs...")
    try:
        github_files = fetch_github_api_docs(dest_dir=sources / "github-api-docs")
    except Exception as e:
        logger.warning(f"GitHub fetch failed: {e}")
        github_files = []

    # 2. Ingest all local sources
    store = VectorStore(persist_dir=kb_dir / "chroma_db")
    total = ingest_local_sources(kb_dir, store)

    # 3. Generate SUMMARY.md
    from summary_generator import generate_summary
    generate_summary(kb_dir, output_path=kb_dir / "SUMMARY.md")
    logger.info("SUMMARY.md regenerated")

    # 4. Generate report
    report = generate_report(
        web_docs=web_report,
        openapi_endpoints=openapi_endpoints,
        github_files=github_files,
        local_chunks=0,
        total_chunks=total,
    )
    logger.info(report)
    return report


if __name__ == "__main__":
    report = run_full_ingestion()
    print(report)
