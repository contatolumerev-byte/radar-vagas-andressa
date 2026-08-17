create extension if not exists pgcrypto;

create table if not exists public.jobs (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  company text not null,
  location text,
  work_mode text,
  salary_min numeric,
  description text not null,
  url text,
  source text,
  score integer check (score between 0 and 100),
  decision text check (decision in ('AUTOAPLICAR','REVISAR','DESCARTAR','BLOQUEADA')),
  reasons jsonb not null default '[]'::jsonb,
  blocks jsonb not null default '[]'::jsonb,
  warnings jsonb not null default '[]'::jsonb,
  status text not null default 'Nova',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.applications (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references public.jobs(id) on delete cascade,
  status text not null default 'Preparando',
  resume_version text,
  submitted_at timestamptz,
  notes text,
  created_at timestamptz not null default now()
);

alter table public.jobs enable row level security;
alter table public.applications enable row level security;

-- A Data API fica disponível somente para a função de servidor.
revoke all on table public.jobs from anon, authenticated;
revoke all on table public.applications from anon, authenticated;
grant usage on schema public to service_role;
grant select, insert, update, delete on table public.jobs to service_role;
grant select, insert, update, delete on table public.applications to service_role;

-- A secret key assume a função service_role e fica somente no servidor.
-- Nunca coloque essa chave no código ou no navegador.
