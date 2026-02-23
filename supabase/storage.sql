-- =============================================================================
-- LiveDocAI – Storage RLS for documents bucket
-- Run this in Supabase SQL Editor after schema.sql.
--
-- BEFORE RUNNING: Create the bucket via Dashboard:
--   Storage → New bucket → name: "documents", Private
--   Optional: 10MB limit, allowed: application/pdf, text/plain
--
-- Path format: {user_id}/{document_id}/{filename}
-- =============================================================================

-- 1. Drop existing policies (idempotent)
drop policy if exists "Users can upload to own folder" on storage.objects;
drop policy if exists "Users can read own files" on storage.objects;
drop policy if exists "Users can update own files" on storage.objects;
drop policy if exists "Users can delete own files" on storage.objects;

-- 3. RLS: Users can only access files in their own folder (path starts with user_id)
-- Path format: {user_id}/{document_id}/{filename}

create policy "Users can upload to own folder"
  on storage.objects for insert
  to authenticated
  with check (
    bucket_id = 'documents'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "Users can read own files"
  on storage.objects for select
  to authenticated
  using (
    bucket_id = 'documents'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "Users can update own files"
  on storage.objects for update
  to authenticated
  using (
    bucket_id = 'documents'
    and (storage.foldername(name))[1] = auth.uid()::text
  )
  with check (
    bucket_id = 'documents'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "Users can delete own files"
  on storage.objects for delete
  to authenticated
  using (
    bucket_id = 'documents'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

