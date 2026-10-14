-- TrustCheck PK schema for Assignment 3
-- Run this in the Supabase SQL Editor once.

create extension if not exists "pgcrypto";

create table if not exists public.app_users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  password_hash text not null,
  full_name text,
  created_at timestamptz not null default now()
);

create table if not exists public.seller_checks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.app_users(id) on delete cascade,
  website text not null,
  phone text not null,
  seller_type text not null,
  seller_name text,
  payment_method text,
  return_policy text,
  risk_level text,
  decision text,
  positive_signals jsonb not null default '[]'::jsonb,
  warning_signals jsonb not null default '[]'::jsonb,
  checklist jsonb not null default '[]'::jsonb,
  summary text,
  status text not null default 'draft',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists seller_checks_user_id_idx on public.seller_checks(user_id);
create index if not exists seller_checks_created_at_idx on public.seller_checks(created_at desc);

alter table public.app_users enable row level security;
alter table public.seller_checks enable row level security;

-- Backend uses the publishable key; allow full access for this student project.
-- Credentials stay on the Python server, not in the React frontend.
drop policy if exists "backend_users_all" on public.app_users;
create policy "backend_users_all"
  on public.app_users
  for all
  to anon, authenticated
  using (true)
  with check (true);

drop policy if exists "backend_checks_all" on public.seller_checks;
create policy "backend_checks_all"
  on public.seller_checks
  for all
  to anon, authenticated
  using (true)
  with check (true);

grant select, insert, update, delete on public.app_users to anon, authenticated;
grant select, insert, update, delete on public.seller_checks to anon, authenticated;
