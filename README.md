# pistrik-kb — PISTRIK Knowledge Base for Claude Code

RAG-powered knowledge base that gives Claude Code semantic search over PISTRIK
(Estonia's waste management information system) compliance documentation.

## Quick Start

```bash
# Clone
git clone <repo-url> /home/rait/dev/gm/pistrik-kb
cd pistrik-kb

# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Initial ingestion (fetches docs, builds vector DB)
python ingest.py

# Register MCP server — add to /home/rait/dev/gm/.mcp.json:
# {
#   "mcpServers": {
#     "pistrik-kb": {
#       "command": "/home/rait/dev/gm/pistrik-kb/.venv/bin/python",
#       "args": ["/home/rait/dev/gm/pistrik-kb/mcp_server.py"]
#     }
#   }
# }
```

## What It Does

| Component | Purpose |
|-----------|---------|
| `ingest.py` | Fetches PISTRIK docs, parses all formats, chunks, embeds into ChromaDB |
| `mcp_server.py` | Exposes 3 tools to Claude Code via MCP |
| `SUMMARY.md` | Auto-generated overview, always loaded by Claude Code |

## MCP Tools

| Tool | Use When |
|------|----------|
| `search_pistrik(query)` | "How does waste confirmation work?" — semantic search |
| `pistrik_endpoint(keyword)` | "What fields does wastenote POST need?" — API lookup |
| `pistrik_update()` | "Update PISTRIK knowledge" — re-fetch and rebuild |

## Sources

| Source | Auto-fetched | Location |
|--------|-------------|----------|
| keskkonnaportaal.ee docs | Yes | `sources/web-docs/` |
| PISTRIK OpenAPI spec | Yes | `sources/openapi/` |
| GitHub API docs (Postman) | Yes | `sources/github-api-docs/` |
| Your notes | Manual | `sources/notes/` |

### Adding Manual Notes

Drop `.md` or `.txt` files into `sources/notes/`, then:
```bash
python ingest.py  # or use pistrik_update() from Claude Code
```

## Updating

From terminal:
```bash
source .venv/bin/activate
python ingest.py
```

From Claude Code: use `pistrik_update()` tool.

If new unsupported file formats appear on keskkonnaportaal.ee, the ingestion
report will warn you with instructions.

## Development

```bash
pip install -r requirements-dev.txt
pytest -v
```

## Tech Stack

- **ChromaDB** — local vector store
- **sentence-transformers** — multilingual embeddings (paraphrase-multilingual-MiniLM-L12-v2)
- **MCP SDK** — Claude Code integration (stdio transport)
- **pymupdf** / **python-docx** — document parsing
