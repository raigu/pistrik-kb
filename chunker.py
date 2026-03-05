"""Chunking logic for different document types.

Each chunker returns a list of dicts:
    {"text": str, "metadata": {"source": str, "section": str, "type": str, ...}}
"""

import json
import re
from datetime import datetime, timezone


def _estimate_tokens(text: str) -> int:
    return len(text.split()) // 4 * 5  # rough: ~0.75 words per token


def chunk_markdown(
    text: str, source: str = "", doc_type: str = "web-doc", max_tokens: int = 1000, url: str = ""
) -> list[dict]:
    """Split markdown by h2/h3 headings. Large sections split at paragraph boundaries."""
    heading_pattern = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
    sections: list[tuple[str, str]] = []

    matches = list(heading_pattern.finditer(text))
    if not matches:
        sections.append(("", text.strip()))
    else:
        if matches[0].start() > 0:
            sections.append(("Intro", text[: matches[0].start()].strip()))
        for i, m in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[m.end() : end].strip()
            sections.append((m.group(2).strip(), body))

    chunks = []
    now = datetime.now(timezone.utc).isoformat()
    for section_name, body in sections:
        if not body.strip():
            continue
        if _estimate_tokens(body) <= max_tokens:
            chunks.append({
                "text": f"{section_name}\n\n{body}" if section_name else body,
                "metadata": {
                    "source": source,
                    "section": section_name,
                    "type": doc_type,
                    "url": url,
                    "ingested_at": now,
                },
            })
        else:
            paragraphs = re.split(r"\n\n+", body)
            # If single paragraph exceeds limit, split by sentences
            expanded = []
            for para in paragraphs:
                if _estimate_tokens(para) > max_tokens:
                    sentences = re.split(r"(?<=\.\s)", para)
                    expanded.extend(sentences)
                else:
                    expanded.append(para)
            current = ""
            for part in expanded:
                if _estimate_tokens(current + part) > max_tokens and current:
                    chunks.append({
                        "text": f"{section_name}\n\n{current.strip()}",
                        "metadata": {
                            "source": source,
                            "section": section_name,
                            "type": doc_type,
                            "url": url,
                            "ingested_at": now,
                        },
                    })
                    current = part + "\n\n"
                else:
                    current += part + "\n\n"
            if current.strip():
                chunks.append({
                    "text": f"{section_name}\n\n{current.strip()}",
                    "metadata": {
                        "source": source,
                        "section": section_name,
                        "type": doc_type,
                        "url": url,
                        "ingested_at": now,
                    },
                })
    return chunks


def chunk_openapi(spec: dict, source: str = "openapi/openapi.json") -> list[dict]:
    """One chunk per endpoint (method + path)."""
    chunks = []
    now = datetime.now(timezone.utc).isoformat()
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.startswith("x-") or method == "parameters":
                continue
            summary = details.get("summary", "")
            op_id = details.get("operationId", "")
            tags = ", ".join(details.get("tags", []))
            params = json.dumps(details.get("parameters", []), indent=2)
            text = (
                f"{method.upper()} {path}\n"
                f"Summary: {summary}\n"
                f"Operation ID: {op_id}\n"
                f"Tags: {tags}\n"
                f"Parameters: {params}\n"
            )
            req_body = details.get("requestBody")
            if req_body:
                text += f"Request Body: {json.dumps(req_body, indent=2)}\n"
            responses = details.get("responses")
            if responses:
                text += f"Responses: {json.dumps(responses, indent=2)}\n"
            chunks.append({
                "text": text,
                "metadata": {
                    "source": source,
                    "section": f"{method.upper()} {path}",
                    "type": "openapi",
                    "method": method.upper(),
                    "path": path,
                    "operation_id": op_id,
                    "tags": tags,
                    "ingested_at": now,
                },
            })
    return chunks


def chunk_postman(collection: dict, source: str = "github-api-docs/collection.json") -> list[dict]:
    """One chunk per Postman request. Handles nested item groups recursively."""
    chunks = []
    now = datetime.now(timezone.utc).isoformat()

    def _process_items(items: list):
        for item in items:
            if "item" in item and "request" not in item:
                _process_items(item["item"])
                continue
            req = item.get("request", {})
            method = req.get("method", "GET")
            url = req.get("url", {})
            raw_url = url.get("raw", str(url)) if isinstance(url, dict) else str(url)
            name = item.get("name", "")
            headers = req.get("header", [])
            body = req.get("body", {})

            text = f"{method} {raw_url}\nName: {name}\n"
            if headers:
                text += f"Headers: {json.dumps(headers, indent=2)}\n"
            if body:
                raw_body = body.get("raw", "")
                if raw_body:
                    text += f"Body: {raw_body}\n"
            chunks.append({
                "text": text,
                "metadata": {
                    "source": source,
                    "section": name,
                    "type": "postman",
                    "method": method,
                    "url": raw_url,
                    "ingested_at": now,
                },
            })

    _process_items(collection.get("item", []))
    return chunks


def chunk_plain_text(
    text: str, source: str = "", doc_type: str = "note", max_tokens: int = 500
) -> list[dict]:
    """Chunk plain text. Try headings first, fall back to paragraph groups."""
    if re.search(r"^#{1,3}\s+", text, re.MULTILINE):
        return chunk_markdown(text, source=source, doc_type=doc_type, max_tokens=max_tokens)

    paragraphs = re.split(r"\n\n+", text)
    chunks = []
    current = ""
    now = datetime.now(timezone.utc).isoformat()
    for para in paragraphs:
        if _estimate_tokens(current + para) > max_tokens and current:
            chunks.append({
                "text": current.strip(),
                "metadata": {"source": source, "section": "", "type": doc_type, "ingested_at": now},
            })
            current = para + "\n\n"
        else:
            current += para + "\n\n"
    if current.strip():
        chunks.append({
            "text": current.strip(),
            "metadata": {"source": source, "section": "", "type": doc_type, "ingested_at": now},
        })
    return chunks
