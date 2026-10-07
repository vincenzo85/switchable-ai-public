#!/usr/bin/env python3
"""Verifica le fonti citate in lcfw/analisi.txt (+ i paper del podcast).

Per ogni arXiv ID: titolo e abstract dal DB di best_paper (sola lettura,
`docker exec … psql`), altrimenti dall'API pubblica di arXiv (3 s tra le
richieste). Stato:
  VERIFICATO     titolo coerente con quello citato
  TITOLO DIVERSO l'ID esiste ma il titolo non corrisponde
  NON TROVATO    l'ID non esiste
Per ogni numero citato nell'analisi si controlla se compare nell'ABSTRACT:
solo quei numeri sono citabili nel deck senza aprire il PDF.
Output: docs/BIBLIOGRAFIA.md + benchmarks/results/bibliography.json
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
from _common import save  # noqa: E402

# appunti dell'autore con le citazioni da verificare (non inclusi in questo repository)
ANALISI = Path(os.environ.get("SAI_BIB_ANALISI", "analisi.txt"))
# revisione manuale (2026-10-03): stesso paper, l'analisi usava un titolo abbreviato
REVIEWED_SAME = {
    "2607.20860": "titolo abbreviato: il paper è 'Which Model Is Actually Serving You? IRIS: …'",
    "2407.16833": "titolo abbreviato: Self-Route è il metodo proposto nel paper",
}
EXTRA = [("2305.02301", "Distilling Step-by-Step! Outperforming Larger Language Models with Less Training Data and Smaller Model Sizes", ""),
         ("2309.06180", "Efficient Memory Management for Large Language Model Serving with PagedAttention", ""),
         ("2609.16818", "InceptionRAG: Stealthy Poisoning Attack Against Retrieval-Augmented Generation", "")]


def parse_analisi() -> list[tuple[str, str, str]]:
    lines = [l.strip() for l in ANALISI.read_text(encoding="utf-8").splitlines()]
    out = []
    for i, l in enumerate(lines):
        m = re.search(r"arXiv:(\d{4}\.\d{4,5})", l)
        if not (l.startswith("Autori") and m):
            continue
        title = next(lines[j] for j in range(i - 1, -1, -1) if lines[j] not in (".", ""))
        claims = ""
        for j in range(i + 1, min(i + 12, len(lines))):
            if lines[j].startswith("Autori"):
                break
            if lines[j].startswith("Risultati"):
                claims = lines[j].split(":", 1)[1].strip()
        out.append((m.group(1), title, claims))
    return out


def from_db(aid: str):
    q = f"select json_build_object('title', title, 'abstract', abstract, 'authors', authors, " \
        f"'date', first_submitted_at) from papers where arxiv_id = '{aid}'"
    try:
        r = subprocess.run(["docker", "exec", "best_paper-postgres-1", "psql", "-U", "best_paper", "-d", "best_paper",
                            "-tAc", q], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):   # DB locale assente: si passa all'API di arXiv
        return None
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


def from_arxiv(aid: str):
    url = f"http://export.arxiv.org/api/query?id_list={aid}"
    with urllib.request.urlopen(url, timeout=30) as r:
        root = ET.fromstring(r.read())
    ns = {"a": "http://www.w3.org/2005/Atom"}
    e = root.find("a:entry", ns)
    if e is None or e.find("a:title", ns) is None or "Error" in (e.findtext("a:title", "", ns)):
        return None
    return {"title": " ".join(e.findtext("a:title", "", ns).split()),
            "abstract": " ".join(e.findtext("a:summary", "", ns).split()),
            "authors": [a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)],
            "date": e.findtext("a:published", "", ns)}


def norm_words(t: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", t.lower()) if len(w) > 2}


def numbers_in(text: str) -> list[str]:
    raw = re.findall(r"\d+(?:[.,]\d+)?\s?(?:%|x|×|volte)?", text)
    return sorted({r.strip() for r in raw if re.search(r"\d", r) and not re.fullmatch(r"20\d\d", r.strip())})


def num_in_abstract(n: str, abstract: str) -> bool:
    core = re.sub(r"\s?(volte|×)$", "x", n.replace(",", "."))
    variants = {core, core.replace("x", "×"), core.replace("x", " times"), core.rstrip("%x×").strip()}
    a = abstract.replace(",", "")
    return any(v and re.search(r"(?<![\d.])" + re.escape(v) + r"(?![\d])", a) for v in variants if len(v.rstrip("%x×")) >= 1)


def main() -> int:
    entries = parse_analisi() + EXTRA
    rows = []
    for aid, title, claims in entries:
        src, meta = "best_paper", from_db(aid)
        if meta is None:
            src = "arXiv API"
            time.sleep(3)
            try:
                meta = from_arxiv(aid)
            except Exception as e:  # noqa: BLE001
                meta, src = None, f"errore arXiv: {e}"
        if meta is None:
            status, overlap = "NON TROVATO", 0.0
        else:
            a, b = norm_words(title), norm_words(meta["title"])
            overlap = len(a & b) / max(1, min(len(a), len(b)))
            status = "VERIFICATO" if overlap >= 0.6 or aid in REVIEWED_SAME else "TITOLO DIVERSO"
        nums = numbers_in(claims)
        found = [n for n in nums if meta and num_in_abstract(n, meta["abstract"])]
        rows.append({"arxiv_id": aid, "cited_title": title, "status": status, "title_overlap": round(overlap, 2),
                     "real_title": meta["title"] if meta else "", "authors": (meta or {}).get("authors", [])[:4],
                     "date": str((meta or {}).get("date", ""))[:10], "source": src,
                     "review_note": REVIEWED_SAME.get(aid, ""),
                     "claims": claims, "numbers_claimed": nums, "numbers_in_abstract": found,
                     "abstract": (meta or {}).get("abstract", "")})
        print(f"{status:<14} {aid} {overlap:.2f} [{src}] numeri nell'abstract {len(found)}/{len(nums)}  {title[:50]}")
    save("bibliography", {"papers": rows})
    write_md(rows)
    return 0


def write_md(rows) -> None:
    L = ["# Bibliografia verificata", "",
         "Generata da `tools/verify_bibliography.py` a partire da `lcfw/analisi.txt` e dai paper del podcast.",
         "Fonte dei metadati: DB di `best_paper` (sola lettura) o API pubblica di arXiv.", "",
         "Regole d'uso nel talk: si citano solo paper **VERIFICATO**; un numero si cita solo se è nella colonna "
         "*numeri nell'abstract*. Gli altri numeri dell'analisi vanno controllati sul PDF prima di usarli.", "",
         "| Stato | arXiv | Titolo reale | Autori | Data | Numeri nell'abstract | Numeri da verificare sul PDF |",
         "|---|---|---|---|---|---|---|"]
    for r in rows:
        auth = ", ".join(a if isinstance(a, str) else str(a) for a in r["authors"][:3]) + (" et al." if len(r["authors"]) > 3 else "")
        rest = [n for n in r["numbers_claimed"] if n not in r["numbers_in_abstract"]]
        L.append(f"| {r['status']} | [{r['arxiv_id']}](https://arxiv.org/abs/{r['arxiv_id']}) | {r['real_title'] or r['cited_title']} | "
                 f"{auth} | {r['date']} | {', '.join(r['numbers_in_abstract']) or '—'} | {', '.join(rest) or '—'} |")
    L += ["", "## Note di revisione manuale", ""]
    L += [f"- `{r['arxiv_id']}`: {r['review_note']}" for r in rows if r.get("review_note")] or ["Nessuna."]
    L += ["", "## Titoli citati nell'analisi che non corrispondono", ""]
    bad = [r for r in rows if r["status"] != "VERIFICATO"]
    L += [f"- `{r['arxiv_id']}`: citato come *{r['cited_title']}*, reale: *{r['real_title'] or 'inesistente'}*" for r in bad] or ["Nessuno."]
    (ROOT / "docs/BIBLIOGRAFIA.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
