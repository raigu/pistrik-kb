#!/usr/bin/env python3
"""MCP server exposing PISTRIK knowledge base tools."""

import json
import logging
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from vectorstore import VectorStore

logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent

server = Server("pistrik-kb")


def _get_store(kb_dir: Path | None = None) -> VectorStore:
    kb_dir = kb_dir or ROOT
    return VectorStore(persist_dir=kb_dir / "chroma_db")


def _load_openapi(kb_dir: Path | None = None) -> dict:
    kb_dir = kb_dir or ROOT
    spec_path = kb_dir / "sources" / "openapi" / "openapi.json"
    if spec_path.exists():
        return json.loads(spec_path.read_text())
    return {}


def handle_search(query: str, top_k: int = 5, kb_dir: Path | None = None) -> list[dict]:
    """Search PISTRIK knowledge base semantically."""
    store = _get_store(kb_dir)
    return store.search(query, top_k=top_k)


def handle_endpoint(keyword: str, kb_dir: Path | None = None) -> list[dict]:
    """Lookup API endpoints by path or keyword."""
    spec = _load_openapi(kb_dir)
    paths = spec.get("paths", {})
    results = []

    for path, methods in paths.items():
        for method, details in methods.items():
            if method.startswith("x-") or method == "parameters":
                continue
            searchable = " ".join([
                path,
                details.get("summary", ""),
                details.get("operationId", ""),
                " ".join(details.get("tags", [])),
            ]).lower()

            if keyword.lower() in searchable:
                results.append({
                    "method": method.upper(),
                    "path": path,
                    "summary": details.get("summary", ""),
                    "operation_id": details.get("operationId", ""),
                    "tags": details.get("tags", []),
                    "parameters": details.get("parameters", []),
                    "request_body": details.get("requestBody"),
                    "responses": details.get("responses"),
                })
    return results


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="search_pistrik",
            description=(
                "Semantic search across PISTRIK knowledge base (web docs, API spec, "
                "Postman examples, manual notes). Use for compliance questions, "
                "design decisions, understanding PISTRIK behavior."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query in Estonian or English"},
                    "top_k": {"type": "integer", "description": "Number of results (default 5)", "default": 5},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="pistrik_endpoint",
            description=(
                "Lookup PISTRIK API endpoints by path or keyword. Returns method, path, "
                "parameters, request/response schemas. Use for precise API questions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Endpoint path (e.g. '/api/v1/wastenote') or keyword (e.g. 'facility')",
                    },
                },
                "required": ["keyword"],
            },
        ),
        Tool(
            name="pistrik_update",
            description=(
                "Re-fetch all PISTRIK sources and rebuild knowledge base. "
                "Fetches latest web docs, OpenAPI spec, and GitHub API docs. "
                "Reports what changed and warns about unsupported file formats."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search_pistrik":
        results = handle_search(
            query=arguments["query"],
            top_k=arguments.get("top_k", 5),
        )
        if not results:
            return [TextContent(type="text", text="No results found.")]
        output = []
        for r in results:
            output.append(
                f"**[{r['metadata'].get('type', '?')}] {r['metadata'].get('source', '?')} "
                f"({r['metadata'].get('section', '')})**\n"
                f"Score: {r.get('score', '?')}\n\n{r['text']}\n"
            )
        return [TextContent(type="text", text="\n---\n".join(output))]

    elif name == "pistrik_endpoint":
        results = handle_endpoint(keyword=arguments["keyword"])
        if not results:
            return [TextContent(type="text", text=f"No endpoints matching '{arguments['keyword']}'.")]
        output = json.dumps(results, indent=2, ensure_ascii=False)
        return [TextContent(type="text", text=output)]

    elif name == "pistrik_update":
        from ingest import run_full_ingestion

        report = run_full_ingestion()
        return [TextContent(type="text", text=report)]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
