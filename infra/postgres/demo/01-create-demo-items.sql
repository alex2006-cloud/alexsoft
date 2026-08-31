-- Demo: create table (run in DBeaver on connection alexsoft)
-- Uses uuid-ossp extension from init/01-extensions.sql

CREATE TABLE IF NOT EXISTS demo_items (
  id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title      TEXT NOT NULL,
  source     TEXT NOT NULL DEFAULT 'dbeaver',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE demo_items IS 'Учебная таблица: DBeaver + Cursor SQLTools';
