-- Add file_hash column for deduplication
-- Run this in Supabase SQL Editor

-- Add file_hash column to documents table
ALTER TABLE public.documents 
ADD COLUMN IF NOT EXISTS file_hash TEXT;

-- Create index for fast hash lookups
CREATE INDEX IF NOT EXISTS documents_file_hash_idx 
ON public.documents(file_hash);

-- Create composite index for user + hash lookups
CREATE INDEX IF NOT EXISTS documents_user_hash_idx 
ON public.documents(user_id, file_hash);

-- Add comment explaining the column
COMMENT ON COLUMN public.documents.file_hash IS 'SHA-256 hash of file content for deduplication';
