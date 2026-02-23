-- =============================================================================
-- LiveDocAI – Clean schema (drops all data, recreates tables)
-- Run this in Supabase SQL Editor to reset and apply the final schema.
-- WARNING: This deletes all data in the affected tables.
-- =============================================================================

-- 1. Drop existing tables (CASCADE removes dependent objects)
drop table if exists public.documents cascade;
drop table if exists public.user_profiles cascade;

-- 2. User profiles (onboarding, name, role)
create table public.user_profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  full_name text,
  company text,
  role text,
  onboarding_completed boolean not null default false,
  created_at timestamptz not null default now()
);

-- 3. Documents (metadata; files in Storage, vectors in Qdrant)
create table public.documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  filename text not null,
  title text,
  storage_path text not null,
  mime_type text not null,
  file_size bigint not null default 0,
  status text not null default 'processing' check (status in ('processing', 'ready', 'failed')),
  created_at timestamptz not null default now()
);

create index documents_user_id_idx on public.documents(user_id);
create index documents_status_idx on public.documents(status);

-- 4. Enable RLS on both tables
alter table public.user_profiles enable row level security;
alter table public.documents enable row level security;

-- 5. RLS policies: user_profiles
create policy "Users can read own profile"
  on public.user_profiles for select using (auth.uid() = id);
create policy "Users can insert own profile"
  on public.user_profiles for insert with check (auth.uid() = id);
create policy "Users can update own profile"
  on public.user_profiles for update using (auth.uid() = id) with check (auth.uid() = id);

-- 6. RLS policies: documents (filter by user_id = auth.uid())
create policy "Users can read own documents"
  on public.documents for select using (auth.uid() = user_id);
create policy "Users can insert own documents"
  on public.documents for insert with check (auth.uid() = user_id);
create policy "Users can update own documents"
  on public.documents for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "Users can delete own documents"
  on public.documents for delete using (auth.uid() = user_id);
