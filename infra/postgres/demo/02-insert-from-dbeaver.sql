-- Demo: first rows (run in DBeaver after 01-create-demo-items.sql)

INSERT INTO demo_items (title, source) VALUES
  ('Первая запись из DBeaver', 'dbeaver'),
  ('Вторая запись из DBeaver', 'dbeaver'),
  ('PostgreSQL 16 работает', 'dbeaver');

-- Check:
-- SELECT id, title, source, created_at FROM demo_items ORDER BY created_at;
