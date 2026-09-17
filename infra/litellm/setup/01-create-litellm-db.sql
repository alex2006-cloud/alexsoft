-- Run once as PostgreSQL superuser (postgres) in DBeaver / psql.
-- Creates a dedicated DB for LiteLLM Admin UI (preferred over schema-in-alexsoft).

CREATE DATABASE litellm OWNER alexsoft;
