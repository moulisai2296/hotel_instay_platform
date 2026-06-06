-- =============================================================================
-- InStayOS — Migration 0001: Enums + Extensions
-- Build order step 1 (a): create all enum types FIRST.
-- Idempotent: safe to re-run in the Supabase SQL Editor.
-- =============================================================================

-- gen_random_uuid() is built-in on PG13+, but pgcrypto guarantees availability.
create extension if not exists pgcrypto;

do $$ begin
  create type staff_role as enum ('staff','dept_manager','hotel_manager','admin');
exception when duplicate_object then null; end $$;

do $$ begin
  create type department_type as enum ('housekeeping','fb','maintenance','concierge','spa','front_desk');
exception when duplicate_object then null; end $$;

do $$ begin
  create type request_status as enum ('pending','assigned','in_progress','completed','escalated','cancelled');
exception when duplicate_object then null; end $$;

do $$ begin
  create type request_priority as enum ('low','medium','high','urgent');
exception when duplicate_object then null; end $$;

do $$ begin
  create type input_mode as enum ('text','voice','chip');
exception when duplicate_object then null; end $$;

do $$ begin
  create type tablet_status as enum ('online','offline','maintenance');
exception when duplicate_object then null; end $$;

do $$ begin
  create type offer_status as enum ('active','expired','claimed');
exception when duplicate_object then null; end $$;

do $$ begin
  create type pms_provider as enum ('cloudbeds','mews','opera','apaleo','manual');
exception when duplicate_object then null; end $$;
