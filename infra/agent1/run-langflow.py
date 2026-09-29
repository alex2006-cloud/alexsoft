"""Launch LangFlow with Windows registry SOCKS proxies disabled for this process."""
from __future__ import annotations

import os
import sys
import urllib.request


def _no_proxies() -> dict:
    return {}


def _no_proxies_nonempty() -> dict:
    return {"all": None}  # type: ignore[dict-item]


def _patch_httpx_no_proxy() -> None:
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
    except Exception:
        pass


def main() -> None:
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"

    urllib.request.getproxies = _no_proxies  # type: ignore[assignment]
    urllib.request.getproxies_environment = _no_proxies_nonempty  # type: ignore[attr-defined]
    for key in list(os.environ):
        if key.lower().endswith("_proxy") and key.lower() not in {"no_proxy"}:
            del os.environ[key]

    _patch_httpx_no_proxy()

    from langflow.__main__ import main as langflow_main

    sys.argv = ["langflow", *sys.argv[1:]]
    langflow_main()


if __name__ == "__main__":
    main()
