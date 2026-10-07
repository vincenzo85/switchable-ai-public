#!/usr/bin/env python3
"""vLLM vs Ollama sullo STESSO modello (Qwen2.5-1.5B-Instruct), stessa GPU.

Ollama serve qwen2.5:1.5b (GGUF Q4_K_M), vLLM serve i pesi BF16 originali:
non è la stessa quantizzazione e il report lo dice. Si misurano:
- TTFT (time to first token, streaming) a richiesta singola;
- throughput aggregato (token/s) a concorrenza 1, 4 e 16 — il caso batch,
  dove PagedAttention + continuous batching dovrebbero fare la differenza.

Lo script avvia vLLM da .venv-vllm, misura e lo spegne. Prima scarica
qwen2.5:7b dalla VRAM di Ollama (8 GB non bastano per tutti e due).
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

from _common import ROOT, pct, save

PROMPT = "Elenca 8 controlli di sicurezza per un gateway LLM aziendale, una riga ciascuno."
VLLM_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"


def stream_chat(base: str, model: str, max_tokens: int) -> dict:
    body = json.dumps({"model": model, "stream": True, "max_tokens": max_tokens, "temperature": 0.0,
                       "stream_options": {"include_usage": True},
                       "messages": [{"role": "user", "content": PROMPT}]}).encode()
    req = urllib.request.Request(f"{base}/v1/chat/completions", data=body, headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    ttft, out_tokens, chunks = None, 0, 0
    with urllib.request.urlopen(req, timeout=600) as r:
        for raw in r:
            line = raw.decode().strip()
            if not line.startswith("data:") or line.endswith("[DONE]"):
                continue
            d = json.loads(line[5:])
            if d.get("choices") and d["choices"][0].get("delta", {}).get("content"):
                chunks += 1
                if ttft is None:
                    ttft = time.monotonic() - t0
            if d.get("usage"):
                out_tokens = d["usage"].get("completion_tokens", out_tokens)
    total = time.monotonic() - t0
    return {"ttft_ms": (ttft or total) * 1000, "total_ms": total * 1000, "tokens_out": out_tokens or chunks}


def concurrent(base: str, model: str, n: int, max_tokens: int) -> dict:
    res, lock = [], threading.Lock()

    def worker():
        r = stream_chat(base, model, max_tokens)
        with lock:
            res.append(r)
    t0 = time.monotonic()
    ts = [threading.Thread(target=worker) for _ in range(n)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    wall = time.monotonic() - t0
    toks = sum(r["tokens_out"] for r in res)
    return {"concurrency": n, "wall_s": wall, "tokens_out": toks, "throughput_tok_s": toks / wall,
            "ttft_p50_ms": pct([r["ttft_ms"] for r in res], 50), "ttft_p95_ms": pct([r["ttft_ms"] for r in res], 95)}


def bench(name: str, base: str, model: str, levels, max_tokens: int) -> dict:
    stream_chat(base, model, 16)                                     # warm-up
    single = [stream_chat(base, model, max_tokens) for _ in range(5)]
    out = {"engine": name, "model": model,
           "single": {"ttft_p50_ms": pct([r["ttft_ms"] for r in single], 50),
                      "total_p50_ms": pct([r["total_ms"] for r in single], 50)},
           "concurrency": [concurrent(base, model, n, max_tokens) for n in levels]}
    for c in out["concurrency"]:
        print(f"{name:<7} c={c['concurrency']:>2} {c['throughput_tok_s']:7.1f} tok/s  TTFT p50 {c['ttft_p50_ms']:.0f} ms")
    return out


def unload_ollama(url: str) -> None:
    try:
        with urllib.request.urlopen(f"{url}/api/ps", timeout=5) as r:
            for m in json.loads(r.read()).get("models", []):
                body = json.dumps({"model": m["name"], "keep_alive": 0}).encode()
                urllib.request.urlopen(urllib.request.Request(f"{url}/api/generate", data=body,
                                                              headers={"Content-Type": "application/json"}), timeout=60).read()
    except Exception as e:  # noqa: BLE001
        print("unload ollama:", e)


def wait_ready(base: str, proc, timeout_s: int = 600) -> None:
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        if proc.poll() is not None:
            raise RuntimeError(f"vLLM è uscito con codice {proc.returncode}")
        try:
            urllib.request.urlopen(f"{base}/v1/models", timeout=2).read()
            return
        except Exception:  # noqa: BLE001
            time.sleep(3)
    raise TimeoutError("vLLM non è partito")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", default="1,4,16")
    ap.add_argument("--max-tokens", type=int, default=200)
    ap.add_argument("--port", type=int, default=8010)   # :8000 è già occupata su questa macchina
    a = ap.parse_args()
    levels = [int(x) for x in a.levels.split(",")]
    ollama = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    results, notes = {}, []

    unload_ollama(ollama)
    results["ollama"] = bench("ollama", ollama, "qwen2.5:1.5b", levels, a.max_tokens)
    unload_ollama(ollama)

    log = ROOT / "benchmarks/results/vllm_server.log"
    cmd = [str(ROOT / ".venv-vllm/bin/vllm"), "serve", VLLM_MODEL, "--host", "127.0.0.1", "--port", str(a.port),
           "--gpu-memory-utilization", "0.70", "--max-model-len", "4096", "--max-num-seqs", "32"]
    with open(log, "w") as lf:
        proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        wait_ready(f"http://127.0.0.1:{a.port}", proc)
        results["vllm"] = bench("vllm", f"http://127.0.0.1:{a.port}", VLLM_MODEL, levels, a.max_tokens)
    except Exception as e:  # noqa: BLE001 — limite documentato, non finto
        notes.append(f"vLLM non misurato: {e} (log: benchmarks/results/vllm_server.log)")
        print(notes[-1])
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
    save("vllm_vs_ollama", {"prompt": PROMPT, "max_tokens": a.max_tokens, "levels": levels, "results": results,
                            "caveat": "Ollama: GGUF Q4_K_M; vLLM: BF16. Stessa architettura e pesi di partenza, "
                                      "quantizzazione diversa.", "notes": notes})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
