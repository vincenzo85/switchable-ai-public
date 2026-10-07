"""Utility condivise dai benchmark: ogni risultato porta con sé QUANDO,
SU QUALE COMMIT e SU QUALE MACCHINA è stato misurato."""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RESULTS = ROOT / "benchmarks" / "results"


def _sh(*cmd: str) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def machine() -> dict:
    return {
        "gpu": _sh("nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"),
        "cpu": _sh("sh", "-c", "grep -m1 'model name' /proc/cpuinfo | cut -d: -f2").strip(),
        "ram_gb": round(int(_sh("sh", "-c", "grep MemTotal /proc/meminfo | awk '{print $2}'") or 0) / 1024 / 1024),
    }


def save(name: str, data: dict) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    meta = {"benchmark": name, "measured_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "git_commit": _sh("git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"), "machine": machine()}
    out = RESULTS / f"{name}.json"
    out.write_text(json.dumps({"meta": meta, **data}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"→ {out.relative_to(ROOT)}")
    return out


def pct(values, p):
    from core.use_cases.report import percentile
    return percentile(list(values), p)
