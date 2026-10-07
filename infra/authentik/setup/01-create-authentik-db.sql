-- Role + database for Authentik in the native PostgreSQL 16 (ADR-0020).
-- Run via infra\authentik\setup-db.ps1 (passes -v u=... -v pw=... -v db=...). Idempotent.
-- CREATE DATABASE cannot run inside a transaction block, so everything is emitted with \gexec.

SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'u', :'pw')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'u') \gexec

SELECT format('ALTER ROLE %I PASSWORD %L', :'u', :'pw') \gexec

SELECT format('CREATE DATABASE %I OWNER %I', :'db', :'u')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'db') \gexec
