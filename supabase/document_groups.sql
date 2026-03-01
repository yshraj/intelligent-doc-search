-- =============================================================================
-- Document Grouping and Tagging Schema
-- Run this in Supabase SQL Editor to add document organization features
-- =============================================================================

-- 1. Document tags table
create table if not exists public.document_tags (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  tag_name text not null,
  tag_category text not null check (tag_category in ('type', 'topic', 'department', 'sensitivity', 'time_period', 'status', 'custom')),
  confidence_score float not null default 1.0 check (confidence_score >= 0 and confidence_score <= 1),
  auto_generated boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index document_tags_document_id_idx on public.document_tags(document_id);
create index document_tags_tag_name_idx on public.document_tags(tag_name);
create index document_tags_tag_category_idx on public.document_tags(tag_category);
create unique index document_tags_unique_idx on public.document_tags(document_id, tag_name, tag_category);

-- 2. Document groups table (hierarchical)
create table if not exists public.document_groups (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  group_name text not null,
  group_type text not null check (group_type in ('type_based', 'topic_based', 'time_based', 'department_based', 'custom')),
  parent_group_id uuid references public.document_groups(id) on delete cascade,
  description text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index document_groups_user_id_idx on public.document_groups(user_id);
create index document_groups_parent_id_idx on public.document_groups(parent_group_id);
create unique index document_groups_unique_idx on public.document_groups(user_id, group_name, parent_group_id);

-- 3. Document group membership (many-to-many)
create table if not exists public.document_group_membership (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  group_id uuid not null references public.document_groups(id) on delete cascade,
  added_at timestamptz not null default now()
);

create index document_group_membership_document_id_idx on public.document_group_membership(document_id);
create index document_group_membership_group_id_idx on public.document_group_membership(group_id);
create unique index document_group_membership_unique_idx on public.document_group_membership(document_id, group_id);

-- 4. Enable RLS
alter table public.document_tags enable row level security;
alter table public.document_groups enable row level security;
alter table public.document_group_membership enable row level security;

-- 5. RLS policies for document_tags (inherit from documents)
create policy "Users can read tags for own documents"
  on public.document_tags for select
  using (
    exists (
      select 1 from public.documents
      where documents.id = document_tags.document_id
      and documents.user_id = auth.uid()
    )
  );

create policy "Users can insert tags for own documents"
  on public.document_tags for insert
  with check (
    exists (
      select 1 from public.documents
      where documents.id = document_tags.document_id
      and documents.user_id = auth.uid()
    )
  );

create policy "Users can update tags for own documents"
  on public.document_tags for update
  using (
    exists (
      select 1 from public.documents
      where documents.id = document_tags.document_id
      and documents.user_id = auth.uid()
    )
  );

create policy "Users can delete tags for own documents"
  on public.document_tags for delete
  using (
    exists (
      select 1 from public.documents
      where documents.id = document_tags.document_id
      and documents.user_id = auth.uid()
    )
  );

-- 6. RLS policies for document_groups
create policy "Users can read own groups"
  on public.document_groups for select
  using (auth.uid() = user_id);

create policy "Users can insert own groups"
  on public.document_groups for insert
  with check (auth.uid() = user_id);

create policy "Users can update own groups"
  on public.document_groups for update
  using (auth.uid() = user_id);

create policy "Users can delete own groups"
  on public.document_groups for delete
  using (auth.uid() = user_id);

-- 7. RLS policies for document_group_membership (inherit from documents and groups)
create policy "Users can read membership for own documents"
  on public.document_group_membership for select
  using (
    exists (
      select 1 from public.documents
      where documents.id = document_group_membership.document_id
      and documents.user_id = auth.uid()
    )
  );

create policy "Users can insert membership for own documents"
  on public.document_group_membership for insert
  with check (
    exists (
      select 1 from public.documents d
      join public.document_groups g on g.id = document_group_membership.group_id
      where d.id = document_group_membership.document_id
      and d.user_id = auth.uid()
      and g.user_id = auth.uid()
    )
  );

create policy "Users can delete membership for own documents"
  on public.document_group_membership for delete
  using (
    exists (
      select 1 from public.documents
      where documents.id = document_group_membership.document_id
      and documents.user_id = auth.uid()
    )
  );

-- 8. Function to get document count for a group
create or replace function get_group_document_count(group_uuid uuid)
returns bigint
language sql
stable
as $$
  select count(*)
  from public.document_group_membership
  where group_id = group_uuid;
$$;

-- 9. Function to update updated_at timestamp
create or replace function update_updated_at_column()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- 10. Triggers for updated_at
create trigger update_document_tags_updated_at
  before update on public.document_tags
  for each row
  execute function update_updated_at_column();

create trigger update_document_groups_updated_at
  before update on public.document_groups
  for each row
  execute function update_updated_at_column();
