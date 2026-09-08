# Demo: бакет через Console и mc

Учебный сценарий — один бакет `alexsoft`, два клиента видят одни и те же объекты.

Исходники лежат в `objects/` и заливаются в префикс `demo/`.

## Часть 0 — залить объекты

MinIO должен быть запущен (`start-minio.ps1`). Из корня репозитория:

```powershell
powershell -ExecutionPolicy Bypass -File infra\minio\seed-demo.ps1
```

Ожидается список:

- `demo/docs/hello.md`
- `demo/docs/notes.txt`
- `demo/docs/sample.json`
- `demo/images/alexsoft-demo.png`

## Часть 1 — Console

1. Открыть http://127.0.0.1:9001 → войти (логин/пароль из `.env`). При первом входе — **Acknowledge** на экране лицензии AGPL.
2. **Buckets** → `alexsoft` → папка `demo/` → `docs/` и `images/`.
3. Открыть `hello.md` — Preview / Download.
4. **Upload** — закинуть любой свой файл в `demo/` (например `from-console.txt`) и убедиться, что он появился.

## Часть 2 — mc (CLI)

```powershell
$mc = "$env:LOCALAPPDATA\MinIO\mc.exe"
& $mc ls --recursive alexsoft/alexsoft/demo
& $mc cat alexsoft/alexsoft/demo/docs/hello.md
```

Если загружали файл из Console — он будет в этом списке.

Залить ещё один объект из CLI:

```powershell
Set-Content -Path $env:TEMP\from-mc.txt -Value "hello from mc"
& $mc cp $env:TEMP\from-mc.txt alexsoft/alexsoft/demo/docs/from-mc.txt
```

В Console обновить список (F5) — появится `from-mc.txt`.

## Часть 3 — снова Console

Скачать `sample.json` и `alexsoft-demo.png` — это те же байты, что в `objects/`.

## Удалить demo (когда надоест)

В Console: выделить префикс `demo/` → Delete.

Или CLI:

```powershell
& $mc rm --recursive --force alexsoft/alexsoft/demo
```

Бакет `alexsoft` можно оставить пустым — им будут пользоваться сервисы позже.
