"""POST JSON con mappatura degli errori di rete su eccezioni di dominio.

urllib della stdlib: niente SDK dei provider, così un cambio di versione di
una libreria non può rompere la rotta di fallback.
"""
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request

from core.domain.errors import ProviderError, ProviderTimeout


def post_json(url: str, payload: dict, *, headers: dict | None = None, timeout_s: float = 60) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        body = e.read()[:300].decode(errors="replace")
        raise ProviderError(f"HTTP {e.code} da {url}: {body}") from e
    except (socket.timeout, TimeoutError) as e:
        raise ProviderTimeout(f"timeout {timeout_s:.0f}s su {url}") from e
    except urllib.error.URLError as e:
        if isinstance(e.reason, (socket.timeout, TimeoutError)):
            raise ProviderTimeout(f"timeout {timeout_s:.0f}s su {url}") from e
        raise ProviderError(f"{url} non raggiungibile: {e.reason}") from e
    except (json.JSONDecodeError, ConnectionError, OSError) as e:
        raise ProviderError(f"risposta non valida da {url}: {e}") from e


def get_json(url: str, *, headers: dict | None = None, timeout_s: float = 5) -> dict:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            return json.loads(r.read() or b"{}")
    except Exception as e:  # noqa: BLE001 — health check: ogni errore = giù
        raise ProviderError(f"{url}: {e}") from e
