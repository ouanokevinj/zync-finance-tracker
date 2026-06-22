-- ============================================================================
-- 001_auth_rls.sql — Multi-user isolation for the Finance Tracker
--
-- Adds per-user ownership to all data tables, a profiles table for unique
-- usernames, and Row-Level Security so the database itself guarantees that a
-- user can only ever touch their own rows (even if the API has a bug).
--
-- Run order:
--   1. This file (creates columns/table/policies). user_id stays NULLABLE here.
--   2. backend/migrate_user.py (creates the first account + backfills user_id).
--   3. The "STEP 4" block at the bottom (locks user_id to NOT NULL).
-- ============================================================================

-- citext gives case-insensitive, still-unique usernames (e.g. "Kevin" == "kevin")
create extension if not exists citext;

-- ── Ownership columns ───────────────────────────────────────────────────────
-- default auth.uid() means inserts made through an authed client are tagged with
-- the caller's id automatically — the API never has to set user_id by hand.
alter table public.earnings
  add column if not exists user_id uuid references auth.users(id) on delete cascade default auth.uid();

alter table public.subscriptions
  add column if not exists user_id uuid references auth.users(id) on delete cascade default auth.uid();

alter table public.spending
  add column if not exists user_id uuid references auth.users(id) on delete cascade default auth.uid();

-- Helpful indexes for per-user lookups
create index if not exists earnings_user_id_idx      on public.earnings(user_id);
create index if not exists subscriptions_user_id_idx on public.subscriptions(user_id);
create index if not exists spending_user_id_idx      on public.spending(user_id);

-- ── Profiles (unique usernames) ─────────────────────────────────────────────
create table if not exists public.profiles (
  id         uuid primary key references auth.users(id) on delete cascade,
  username   citext unique not null,
  created_at timestamptz not null default now()
);

-- ── Row-Level Security ──────────────────────────────────────────────────────
alter table public.earnings      enable row level security;
alter table public.subscriptions enable row level security;
alter table public.spending      enable row level security;
alter table public.profiles      enable row level security;

-- One "for all" policy per data table: a row is visible/writable only when it
-- belongs to the current JWT's user. with check blocks inserting/updating rows
-- owned by someone else.
drop policy if exists "own earnings" on public.earnings;
create policy "own earnings" on public.earnings
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists "own subscriptions" on public.subscriptions;
create policy "own subscriptions" on public.subscriptions
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists "own spending" on public.spending;
create policy "own spending" on public.spending
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

-- A user can read/insert only their own profile row.
drop policy if exists "own profile" on public.profiles;
create policy "own profile" on public.profiles
  for all using (id = auth.uid()) with check (id = auth.uid());

-- ============================================================================
-- STEP 4 — run AFTER backend/migrate_user.py has backfilled existing rows.
-- Uncomment and execute to make ownership mandatory going forward.
-- ============================================================================
-- alter table public.earnings      alter column user_id set not null;
-- alter table public.subscriptions alter column user_id set not null;
-- alter table public.spending      alter column user_id set not null;
