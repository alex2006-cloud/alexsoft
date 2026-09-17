"""Launch LiteLLM proxy with Windows registry SOCKS proxies disabled for this process."""
from __future__ import annotations

import os
import sys
import traceback
import urllib.request
from pathlib import Path

BOOT_LOG = Path(__file__).resolve().parent / "boot.log"


def _no_proxies() -> dict:
    return {}


def _log(msg: str) -> None:
    try:
        with BOOT_LOG.open("a", encoding="utf-8") as f:
            f.write(msg.rstrip() + "\n")
    except Exception:
        pass


def _load_repo_dotenv() -> None:
    """Load AI keys from repo .env into this process (Start-Process may drop them)."""
    candidates = []
    override = os.environ.get("ALEXSOFT_REPO_ROOT")
    if override:
        candidates.append(Path(override) / ".env")
    marker = Path(__file__).resolve().parent / "repo-root.txt"
    if marker.is_file():
        candidates.append(Path(marker.read_text(encoding="utf-8").strip()) / ".env")
    for env_path in candidates:
        if not env_path.is_file():
            continue
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key in {
                "LITELLM_MASTER_KEY",
                "LITELLM_DATABASE_URL",
                "LITELLM_SALT_KEY",
                "DASHSCOPE_API_KEY",
                "DASHSCOPE_API_BASE",
                "OPENAI_API_KEY",
                "ANTHROPIC_API_KEY",
            }:
                os.environ[key] = val
        break

    litellm_db = os.environ.get("LITELLM_DATABASE_URL", "").strip()
    if os.environ.get("LITELLM_SKIP_DB", "").strip() == "1":
        os.environ.pop("LITELLM_DATABASE_URL", None)
        os.environ.pop("DATABASE_URL", None)
        _log("mode=skip_db")
    elif litellm_db:
        os.environ["DATABASE_URL"] = litellm_db
        # Do not log the URL (contains password).
        _log("mode=with_db url_set=1")
    else:
        _log("mode=no_db_url")
    os.environ.setdefault("DISABLE_SCHEMA_UPDATE", "true")
    os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")


def _patch_prisma_engine_write() -> None:
    """Work around LiteLLM bug with prisma>=0.13 (_Prisma__engine vs _engine).

    See https://github.com/BerriAI/litellm/issues/39114
    """
    try:
        from litellm.proxy.db.prisma_client import PrismaWrapper

        @staticmethod
        def _write_engine(prisma_client, engine):  # type: ignore[no-untyped-def]
            prisma_client._engine = engine

        PrismaWrapper._write_engine = _write_engine  # type: ignore[method-assign]
        _log("prisma_engine_patch=ok")
    except Exception as e:
        _log(f"prisma_engine_patch=fail {type(e).__name__}")


def _patch_prisma_engine_spawn() -> None:
    """Windows-safe query-engine spawn: 127.0.0.1 + DEVNULL stdio.

    Under Start-Process the parent often has no usable console. Prisma passes
    sys.stdout/sys.stderr into Popen; a broken handle makes the engine exit
    right after /status succeeds, so later SELECT 1 gets ConnectError.
    Also prefer 127.0.0.1 over localhost (IPv6 ::1 mismatches on some hosts).
    """
    try:
        import subprocess

        from prisma._builder import dumps
        from prisma.engine import _query as prisma_query
        from prisma.engine import utils
        from prisma.utils import DEBUG, _env_bool

        def _spawn_windows(self, *, file, datasources):  # type: ignore[no-untyped-def]
            port = utils.get_open_port()
            self.url = f"http://127.0.0.1:{port}"

            env = os.environ.copy()
            env.update(
                PRISMA_DML_PATH=str(self.dml_path.absolute()),
                RUST_LOG="error",
                RUST_LOG_FORMAT="json",
                PRISMA_CLIENT_ENGINE_TYPE="binary",
                PRISMA_ENGINE_PROTOCOL="graphql",
            )
            if DEBUG:
                env.update(RUST_LOG="info")
            if datasources is not None:
                env.update(OVERWRITE_DATASOURCES=dumps(datasources))
            if self._log_queries:
                env.update(LOG_QUERIES="y")

            args = [
                str(file.absolute()),
                "-p",
                str(port),
                "--enable-metrics",
                "--enable-raw-queries",
            ]
            if _env_bool("__PRISMA_PY_PLAYGROUND"):
                env.update(RUST_LOG="info")
                args.append("--enable-playground")

            self.process = subprocess.Popen(
                args,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            _log(f"prisma_engine_spawn port={port} pid={self.process.pid}")
            return self.url, self.process

        prisma_query.BaseQueryEngine._spawn_process = _spawn_windows  # type: ignore[method-assign]
        _log("prisma_spawn_patch=ok")
    except Exception as e:
        _log(f"prisma_spawn_patch=fail {type(e).__name__}: {e}")


def _patch_httpx_no_proxy() -> None:
    """Force httpx to ignore Windows registry SOCKS (breaks Prisma query-engine on localhost)."""
    try:
        import httpx

        def _wrap_init(orig):
            def _init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
                kwargs["trust_env"] = False
                kwargs["proxy"] = None
                return orig(self, *args, **kwargs)

            return _init

        httpx.Client.__init__ = _wrap_init(httpx.Client.__init__)  # type: ignore[method-assign]
        httpx.AsyncClient.__init__ = _wrap_init(httpx.AsyncClient.__init__)  # type: ignore[method-assign]
        _log("httpx_no_proxy_patch=ok")
    except Exception as e:
        _log(f"httpx_no_proxy_patch=fail {type(e).__name__}")


def main() -> None:
    try:
        BOOT_LOG.write_text("boot_start\n", encoding="utf-8")
    except Exception:
        pass

    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

    # Non-empty map so callers using `getproxies_environment() or getproxies_registry()`
    # never fall through to Windows SOCKS registry.
    def _no_proxies_nonempty() -> dict:
        return {"all": None}  # type: ignore[dict-item]

    urllib.request.getproxies = _no_proxies  # type: ignore[assignment]
    urllib.request.getproxies_environment = _no_proxies_nonempty  # type: ignore[attr-defined]
    for key in list(os.environ):
        if key.lower().endswith("_proxy") and key.lower() not in {"no_proxy"}:
            del os.environ[key]

    _load_repo_dotenv()
    _patch_httpx_no_proxy()
    _patch_prisma_engine_spawn()
    _patch_prisma_engine_write()

    # Append LiteLLM logs to boot.log without replacing fileno (engine spawn
    # used to inherit a broken console handle under Start-Process).
    class _Tee:
        def __init__(self, stream, path: Path):
            self._stream = stream
            self._path = path
            self._buffer = getattr(stream, "buffer", None)

        def write(self, data: str) -> int:
            try:
                with self._path.open("a", encoding="utf-8", errors="replace") as f:
                    f.write(data)
            except Exception:
                pass
            try:
                return self._stream.write(data)
            except Exception:
                return len(data)

        def flush(self) -> None:
            try:
                self._stream.flush()
            except Exception:
                pass

        def isatty(self) -> bool:
            return False

        def fileno(self) -> int:
            # Do not hand Start-Process / headless stdio to child processes.
            raise OSError("tee has no fileno")

        @property
        def encoding(self) -> str:
            return getattr(self._stream, "encoding", "utf-8") or "utf-8"

        @property
        def errors(self) -> str | None:
            return getattr(self._stream, "errors", "replace")

    sys.stdout = _Tee(sys.stdout, BOOT_LOG)  # type: ignore[assignment]
    sys.stderr = _Tee(sys.stderr, BOOT_LOG)  # type: ignore[assignment]

    try:
        from litellm import run_server

        sys.argv = ["litellm", *sys.argv[1:]]
        _log("calling_run_server")
        run_server()
    except SystemExit as e:
        _log(f"system_exit code={e.code}")
        raise
    except Exception:
        _log(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
