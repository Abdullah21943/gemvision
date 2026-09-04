-- GemVision Supabase schema
-- Run this in the Supabase project's SQL editor (Project -> SQL Editor -> New query).
-- Covers Modules 1 (Auth) and 5 (Scan History) from the project proposal.

-- 1. Profiles ---------------------------------------------------------------
-- Mirrors auth.users with app-specific fields, auto-created on signup.

create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text not null,
  display_name text,
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "Users can view their own profile"
  on public.profiles for select
  using (auth.uid() = id);

create policy "Users can update their own profile"
  on public.profiles for update
  using (auth.uid() = id);

-- Auto-insert a profile row whenever a new auth user is created.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email);
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- 2. Scan history ------------------------------------------------------------
-- One row per gemstone scan: CNN result + price estimate + the image.

create table if not exists public.scans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  gem_type text not null,
  confidence numeric not null check (confidence >= 0 and confidence <= 1),
  top_k jsonb,
  carat numeric,
  cut text,
  clarity text,
  color text,
  estimated_price numeric,
  price_range_low numeric,
  price_range_high numeric,
  image_url text,
  created_at timestamptz not null default now()
);

create index if not exists scans_user_id_created_at_idx
  on public.scans (user_id, created_at desc);

alter table public.scans enable row level security;

create policy "Users can view their own scans"
  on public.scans for select
  using (auth.uid() = user_id);

create policy "Users can insert their own scans"
  on public.scans for insert
  with check (auth.uid() = user_id);

create policy "Users can delete their own scans"
  on public.scans for delete
  using (auth.uid() = user_id);

-- 3. Storage bucket for scan images ------------------------------------------
-- Create the bucket itself in the Supabase dashboard (Storage -> New bucket
-- -> name it "scan-images", keep it private), then run this to scope access
-- to each user's own folder: scan-images/<user_id>/<filename>.

insert into storage.buckets (id, name, public)
values ('scan-images', 'scan-images', false)
on conflict (id) do nothing;

create policy "Users can upload to their own folder"
  on storage.objects for insert
  with check (
    bucket_id = 'scan-images'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "Users can view their own images"
  on storage.objects for select
  using (
    bucket_id = 'scan-images'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "Users can delete their own images"
  on storage.objects for delete
  using (
    bucket_id = 'scan-images'
    and (storage.foldername(name))[1] = auth.uid()::text
  );
