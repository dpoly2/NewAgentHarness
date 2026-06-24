# Document RAG

_Generated on 2026-06-24 03:23 UTC._

## Overview

ArchonHub's document RAG stack turns uploaded files into parsed text, chunked embeddings, and semantic search results. It combines SQLite for metadata with ChromaDB for vector storage.

## Architecture

```
file upload
  → file_processor.save_file(...)
  → uploaded_files row
  → parse_file(file_id)
  → parsed_content stored
  → document_rag.embed_file(file_id)
  → chunk_text(...)
  → OpenAI embeddings.create(...)
  → ChromaDB collection.add(...)
  → file_chunks rows
  → /api/files/_search semantic retrieval
```

## Core configuration

- Chunk size: 512 pseudo-tokens.
- Chunk overlap: 50 pseudo-tokens.
- Embedding model: `text-embedding-3-small`.
- Embedding dimension: 1536.
- Vector store path: `.agents/agentharness/memory/chromadb`.

## How it works (step by step)

1. The client uploads a file.
2. The file processor stores metadata and raw bytes under the local upload path.
3. The parser extracts text and metadata into the `uploaded_files` row.
4. `DocumentEmbedder.chunk_text(...)` slices text into overlapping segments.
5. OpenAI embeddings are generated in batches of up to 100 chunks.
6. ChromaDB stores embeddings while SQLite stores the chunk metadata.
7. Search requests embed the query and retrieve top chunks from ChromaDB.

## API Endpoints Used

| Endpoint | Purpose |
| --- | --- |
| `POST /api/files/upload` | Upload + parse |
| `GET /api/files` | List uploads |
| `GET /api/files/{file_id}` | Inspect one file |
| `POST /api/files/{file_id}/embed` | Embed parsed text |
| `GET /api/files/_search` | Semantic search |
| `GET /api/documents*` | Structured documents separate from raw uploads |

## Error Handling

- If ChromaDB is not installed, embedding/search returns a disabled error instead of pretending success.
- If `OPENAI_API_KEY` is absent, embeddings are disabled.
- Empty parsed content causes embedding to fail fast.
- Embedding count mismatches are treated as hard errors to avoid corrupt vector rows.

## Relationship to the rest of the system

- Uploaded files are the ingestion layer.
- `documents` are curated authored records.
- `knowledge_base` is a lighter structured reference store.
- Search results can be used by Inez, document views, or future agent workflows.

## Related Documentation

- [Documents API](../api/documents.md)
- [Database schema](../architecture/database-schema.md)
- [iOS views](../ios/views.md)

## Source References

- `.agents/agentharness/app/v3/document_rag.py`
- `.agents/agentharness/app/v3/file_processor.py`
- `.agents/agentharness/app/v3/add_file_uploads.py`
- `.agents/agentharness/app/v3/routers/files.py`

## Implementation Checklist

- Confirm `document rag` responses use ISO 8601 UTC timestamps.
- Confirm Bearer JWT is attached on authenticated requests.
- Confirm error payloads use `{"detail": "..."}`.
- Confirm the iOS client can decode optional/null fields safely.
- Confirm background jobs publish notifications or run status events when relevant.
- Confirm SQLite writes update `created_at` / `updated_at` consistently when the table includes them.
- Confirm WebSocket listeners gracefully handle reconnects and unauthorized closes.
- Confirm scheduler or automation side effects are idempotent where retries can occur.
- Confirm prompt, memory, and document payloads are trimmed before persistence when the source code enforces size caps.
- Confirm optional modules fail closed with `503` or `500` rather than silently corrupting state.

## Operational Notes

- `document rag` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.
