create table if not exists public.agents (
    id text primary key not null,
    owner_id text,
    name text not null,
    goal text not null,
    description text not null,
    capabilities jsonb not null default '[]'::jsonb,
    knowledge_sources jsonb not null default '[]'::jsonb,
    channels jsonb not null default '[]'::jsonb,
    configuration jsonb not null default '{}'::jsonb,
    status text not null default 'DRAFT',
    version text not null default '1.0',
    created_at text not null,
    updated_at text not null
);

alter table public.agents enable row level security;

create policy "agents_select_own_rows"
on public.agents
for select
using (
    owner_id = current_setting('request.jwt.claims', true)::json->>'sub'
);

create policy "agents_insert_own_rows"
on public.agents
for insert
with check (
    owner_id = current_setting('request.jwt.claims', true)::json->>'sub'
);

create policy "agents_update_own_rows"
on public.agents
for update
using (
    owner_id = current_setting('request.jwt.claims', true)::json->>'sub'
)
with check (
    owner_id = current_setting('request.jwt.claims', true)::json->>'sub'
);

create policy "agents_delete_own_rows"
on public.agents
for delete
using (
    owner_id = current_setting('request.jwt.claims', true)::json->>'sub'
);