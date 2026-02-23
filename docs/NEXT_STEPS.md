# LiveDocAI – Next Steps & Data Model

## How User Filtering Works

### User ID
- **Source:** JWT `sub` claim = `auth.users.id` (UUID from Supabase Auth)
- **Backend:** `get_current_user()` → `user.id` (or `get_current_user_id()`)
- **Use:** Every document/chat API scopes by `user_id`

### Document Filtering
1. **Supabase (PostgreSQL):** Each row has `user_id`. RLS policies enforce `auth.uid() = user_id`.
2. **Qdrant (vectors):** Each chunk payload includes `user_id` and `document_id`. Filter: `user_id = "<uuid>"` (and optionally `document_id`).
3. **Supabase Storage:** Bucket RLS or path prefix `{user_id}/` so users only access their files.

---

## Tables (Current Schema)

| Table | Purpose |
|-------|---------|
| `user_profiles` | Onboarding, name, role, company |
| `documents` | Document metadata (filename, storage_path, status, etc.) |

### documents columns
| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid | PK, auto-generated |
| `user_id` | uuid | FK → auth.users; **filter key** |
| `filename` | text | Original filename |
| `title` | text | Display title (default from filename) |
| `storage_path` | text | Path in Supabase Storage |
| `mime_type` | text | e.g. application/pdf, text/plain |
| `file_size` | bigint | Bytes |
| `status` | text | processing \| ready \| failed |
| `created_at` | timestamptz | Upload time |

---

## Implementation Order

| # | Task | Status |
|---|------|--------|
| 1 | Run updated `supabase/schema.sql` (adds `documents` table) | Done |
| 2 | Create Storage bucket + run `supabase/storage.sql` | Pending |
| 3 | Implement `/documents` list – query by `user_id` | Done |
| 4 | Implement `/documents/upload` – validate, upload to Storage, insert row | Done |
| 5 | Implement PDF/text extraction + chunking | Pending |
| 6 | Set up Qdrant Cloud, create collection | Pending |
| 7 | Embed chunks (Gemini), upsert to Qdrant with `user_id` in payload | Pending |
| 8 | Implement `/chat` – filter Qdrant by `user_id`, RAG with Gemini | Pending |
| 9 | Implement `/documents/{id}` get + delete | Pending |
| 10 | Frontend: upload UI, document list, chat UI | Pending |

---

## Qdrant Filtering (RAG)

When querying vectors for RAG:

```python
# Filter to only this user's chunks (and optionally a specific document)
qdrant_client.search(
    collection_name="livedocai_chunks",
    query_vector=embedding,
    query_filter=Filter(
        must=[
            FieldCondition(key="user_id", match=MatchValue(value=user_id)),
            # Optional: FieldCondition(key="document_id", match=MatchValue(value=doc_id))
        ]
    ),
    limit=5
)
```

---

## No New Tables Needed (for Phase 1)

The current schema covers Phase 1. Optional later:
- `chat_sessions` – if you want persistent chat history
- `messages` – if you want to store Q&A pairs
