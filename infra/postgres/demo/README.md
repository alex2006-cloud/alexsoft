# Demo: таблица через DBeaver и Cursor

Учебный сценарий — одна БД `alexsoft`, два клиента видят одни и те же данные.

## Часть 1 — DBeaver

1. Подключение **alexsoft** → SQL-редактор.
2. Выполнить `01-create-demo-items.sql` (Ctrl+Enter на весь файл или по блокам).
3. Выполнить `02-insert-from-dbeaver.sql`.
4. Проверка:

```sql
SELECT id, title, source, created_at
FROM demo_items
ORDER BY created_at;
```

Должно быть **3 строки**, `source = dbeaver`.

## Часть 2 — Cursor

1. SQLTools → подключение **alexsoft (local)** → Connect.
2. Открыть `infra/postgres/demo/03-view-and-insert-from-cursor.sql`.
3. Выделить первый `SELECT` → Run (`Ctrl+E`, `Ctrl+E`) — те же 3 строки из DBeaver.
4. Выделить `INSERT` → Run.
5. Выделить второй `SELECT` → Run — должно быть **5 строк** (3 + 2).

## Часть 3 — снова DBeaver (опционально)

Обновить таблицу (F5 или повторный SELECT) — появятся строки с `source = cursor`.

## Удалить demo (когда надоест)

```sql
DROP TABLE IF EXISTS demo_items;
```
