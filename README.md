# pistrik-kb — PISTRIK Knowledge Base for Claude Code

**Audience:** Developers integrating with the PISTRIK API who use Claude Code as their coding assistant.

Give Claude Code instant access to PISTRIK knowledge via RAG — instead of scanning full documents, it retrieves the most relevant chunks in milliseconds. Claude can answer compliance questions, look up API endpoints, and make informed design decisions without you searching docs manually.

- **Semantic search** across web docs, OpenAPI spec, Postman collections, and your own notes
- **[Official PISTRIK API specification](https://pistrikkoolitus.envir.ee/docs)** — endpoint lookup by keyword or path, with parameters and schemas
- **One-command update** to re-fetch all sources and rebuild the knowledge base
- Runs locally via MCP (Model Context Protocol) — no external APIs, no data leaves your machine
- Developed for Claude Code, but should work with any MCP-compatible AI coding assistant

## Setup

```bash
cd /path/to/pistrik-kb

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Fetch sources and build vector DB
python ingest.py
```

Register the MCP server by adding to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "pistrik-kb": {
      "command": "<path-to-pistrik-kb>/.venv/bin/python",
      "args": ["<path-to-pistrik-kb>/mcp_server.py"]
    }
  }
}
```

Restart Claude Code to pick up the new MCP server.

## Usage

Claude Code gets three tools automatically:

| Tool | Use When |
|------|----------|
| `search_pistrik(query)` | Compliance questions, design decisions — semantic search |
| `pistrik_endpoint(keyword)` | API field requirements, endpoint details — structured lookup |
| `pistrik_update()` | Re-fetch all sources and rebuild the knowledge base |

## Sources

| Source | Auto-fetched | Location |
|--------|-------------|----------|
| keskkonnaportaal.ee docs + attachments | Yes | `sources/web-docs/` |
| PISTRIK OpenAPI spec | Yes | `sources/openapi/` |
| GitHub Postman collections | Yes | `sources/github-api-docs/` |
| Manual notes (emails, meetings, chats) | No | `sources/notes/` |

### Adding Notes

Drop `.md` or `.txt` files into `sources/notes/`, then run `python ingest.py` (or use `pistrik_update()` from Claude Code).

Examples of useful notes:
- Custom business rules specific to your PISTRIK integration
- Meeting notes from compliance or integration discussions
- Observations about undocumented API behavior
- Copy-pasted emails containing relevant integration details

## How It Works

| Component | Purpose |
|-----------|---------|
| `ingest.py` | Fetches remote sources, parses all formats, chunks, embeds into ChromaDB |
| `mcp_server.py` | Exposes tools to Claude Code via MCP (stdio transport) |
| `SUMMARY.md` | Auto-generated overview, loaded into Claude Code context |

## Development

```bash
pip install -r requirements-dev.txt
pytest -v
```

## Tech Stack

- **ChromaDB** — local vector store
- **sentence-transformers** — multilingual embeddings (paraphrase-multilingual-MiniLM-L12-v2)
- **MCP SDK** — Claude Code integration (stdio)
- **pymupdf** / **python-docx** — document parsing
