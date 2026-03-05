# PISTRIK Knowledge Base

This directory contains the PISTRIK compliance knowledge base for Claude Code.

## MCP Tools

- `search_pistrik(query, top_k)` - semantic search across all sources
- `pistrik_endpoint(keyword)` - precise API endpoint lookup from OpenAPI spec
- `pistrik_update()` - re-fetch sources and rebuild the knowledge base

## Sources

- `sources/web-docs/` - keskkonnaportaal.ee documentation (auto-fetched)
- `sources/openapi/` - PISTRIK OpenAPI spec (auto-fetched)
- `sources/github-api-docs/` - Postman collections from GitHub (auto-fetched)
- `sources/notes/` - manual notes (emails, chats, meeting notes)

## Updating

Run `pistrik_update()` tool or `python ingest.py` from terminal.

## Adding Notes

Drop `.md` or `.txt` files into `sources/notes/`, then run ingestion.
