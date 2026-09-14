-- Enable PostgreSQL statement logging for data-changing SQL (DDL + INSERT/UPDATE/DELETE).
-- Requires a superuser session (role postgres). Reload is enough; no full restart.
-- Run via: infra/postgres/enable-change-logging.ps1

ALTER SYSTEM SET log_statement = 'mod';
ALTER SYSTEM SET log_line_prefix = '%t [%p] %u@%d ';
SELECT pg_reload_conf() AS reloaded;
SHOW log_statement;
SHOW log_directory;
SHOW data_directory;
