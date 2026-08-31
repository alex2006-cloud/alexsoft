-- Run as superuser (postgres) after installing PostgreSQL 16.
-- Use the same password as POSTGRES_PASSWORD in .env (replace change-me below).
--
-- DBeaver: run part 1 and part 2 SEPARATELY (Ctrl+Enter on each block).
-- CREATE DATABASE cannot run in the same transaction as other statements.

-- === Part 1: role (run first) ===
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'alexsoft') THEN
    CREATE ROLE alexsoft WITH LOGIN PASSWORD 'change-me';
  END IF;
END
$$;

-- === Part 2: database (run second, alone) ===
-- CREATE DATABASE alexsoft OWNER alexsoft;
