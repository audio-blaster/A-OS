-- Reconcile the live agents table with the Agent repository contract.
-- Existing values are preserved; invalid casts or ownership data fail the migration.

create table if not exists public.agents (
    id uuid primary key,
    owner_id uuid not null references auth.users(id) on delete cascade,
    name text not null,
    goal text not null default '',
    description text not null default '',
    capabilities jsonb not null default '[]'::jsonb,
    knowledge_sources jsonb not null default '[]'::jsonb,
    channels jsonb not null default '[]'::jsonb,
    configuration jsonb not null default '{}'::jsonb,
    status text not null default 'DRAFT',
    version text not null default '1.0',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

do $$
begin
    if to_regclass('public.agents') is null then
        raise exception 'public.agents table was not created';
    end if;

    if exists (
        select 1 from information_schema.columns
        where table_schema = 'public' and table_name = 'agents' and column_name = 'user_id'
    ) and exists (
        select 1 from information_schema.columns
        where table_schema = 'public' and table_name = 'agents' and column_name = 'owner_id'
    ) then
        raise exception 'public.agents contains both user_id and owner_id; resolve ownership data before migration';
    end if;

    if exists (
        select 1 from information_schema.columns
        where table_schema = 'public' and table_name = 'agents' and column_name = 'user_id'
    ) then
        alter table public.agents rename column user_id to owner_id;
    end if;

    if not exists (
        select 1 from information_schema.columns
        where table_schema = 'public' and table_name = 'agents' and column_name = 'id'
    ) then
        raise exception 'public.agents.id is missing; existing rows cannot be preserved safely';
    end if;
end $$;

do $$
begin
    if exists (select 1 from public.agents where owner_id is null) then
        raise exception 'public.agents contains rows with null owner_id; ownership must be repaired before migration';
    end if;

    if exists (
        select 1 from public.agents
        where status not in ('DRAFT', 'TESTING', 'PUBLISHED')
    ) then
        raise exception 'public.agents contains an invalid status; expected DRAFT, TESTING, or PUBLISHED';
    end if;
end $$;

alter table public.agents
    add column if not exists owner_id uuid,
    add column if not exists name text not null default '',
    add column if not exists goal text not null default '',
    add column if not exists description text not null default '',
    add column if not exists capabilities jsonb not null default '[]'::jsonb,
    add column if not exists knowledge_sources jsonb not null default '[]'::jsonb,
    add column if not exists channels jsonb not null default '[]'::jsonb,
    add column if not exists configuration jsonb not null default '{}'::jsonb,
    add column if not exists status text not null default 'DRAFT',
    add column if not exists version text not null default '1.0',
    add column if not exists created_at timestamptz not null default now(),
    add column if not exists updated_at timestamptz not null default now();

do $$
declare
    column_type text;
begin
    select udt_name into column_type from information_schema.columns
    where table_schema = 'public' and table_name = 'agents' and column_name = 'id';
    if column_type <> 'uuid' then
        alter table public.agents alter column id type uuid using id::uuid;
    end if;

    select udt_name into column_type from information_schema.columns
    where table_schema = 'public' and table_name = 'agents' and column_name = 'owner_id';
    if column_type <> 'uuid' then
        alter table public.agents alter column owner_id type uuid using owner_id::uuid;
    end if;

    foreach column_type in array array['capabilities', 'knowledge_sources', 'channels', 'configuration'] loop
        if exists (
            select 1 from information_schema.columns
            where table_schema = 'public' and table_name = 'agents' and column_name = column_type
              and udt_name <> 'jsonb'
        ) then
            execute format(
                'alter table public.agents alter column %I type jsonb using %I::jsonb',
                column_type, column_type
            );
        end if;
    end loop;

    select udt_name into column_type from information_schema.columns
    where table_schema = 'public' and table_name = 'agents' and column_name = 'created_at';
    if column_type <> 'timestamptz' then
        alter table public.agents alter column created_at type timestamptz using created_at::timestamptz;
    end if;

    select udt_name into column_type from information_schema.columns
    where table_schema = 'public' and table_name = 'agents' and column_name = 'updated_at';
    if column_type <> 'timestamptz' then
        alter table public.agents alter column updated_at type timestamptz using updated_at::timestamptz;
    end if;
end $$;

alter table public.agents
    alter column owner_id set not null,
    alter column name set not null,
    alter column goal set not null,
    alter column description set not null,
    alter column capabilities set not null,
    alter column knowledge_sources set not null,
    alter column channels set not null,
    alter column configuration set not null,
    alter column status set not null,
    alter column version set not null,
    alter column created_at set not null,
    alter column updated_at set not null;

alter table public.agents
    drop constraint if exists agents_status_check;

alter table public.agents
    add constraint agents_status_check
    check (status in ('DRAFT', 'TESTING', 'PUBLISHED'));

alter table public.agents
    drop constraint if exists agents_owner_id_fkey;

alter table public.agents
    add constraint agents_owner_id_fkey
    foreign key (owner_id) references auth.users(id) on delete cascade;

create index if not exists agents_owner_updated_at_idx
on public.agents (owner_id, updated_at desc);

alter table public.agents enable row level security;

drop policy if exists agents_select_own_rows on public.agents;
drop policy if exists agents_insert_own_rows on public.agents;
drop policy if exists agents_update_own_rows on public.agents;
drop policy if exists agents_delete_own_rows on public.agents;

create policy agents_select_own_rows on public.agents
for select using (owner_id = auth.uid());

create policy agents_insert_own_rows on public.agents
for insert with check (owner_id = auth.uid());

create policy agents_update_own_rows on public.agents
for update using (owner_id = auth.uid())
with check (owner_id = auth.uid());

create policy agents_delete_own_rows on public.agents
for delete using (owner_id = auth.uid());