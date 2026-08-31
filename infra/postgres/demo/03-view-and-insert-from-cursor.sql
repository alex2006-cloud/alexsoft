-- Demo: view and insert from Cursor (SQLTools)
-- 1) Run SELECT to see rows from DBeaver
-- 2) Run INSERT block
-- 3) Run SELECT again

SELECT id, title, source, created_at
FROM demo_items
ORDER BY created_at;

INSERT INTO demo_items (title, source) VALUES
  ('Запись из Cursor SQLTools', 'cursor'),
  ('Ещё одна из Cursor', 'cursor');

SELECT id, title, source, created_at
FROM demo_items
ORDER BY created_at;
