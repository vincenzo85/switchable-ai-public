"""Test di confine architetturale (vedi DEFINITION_OF_DONE.md):
core/ può importare solo la standard library e altri moduli di core/ —
mai adapters/, mai pacchetti esterni infrastrutturali.

Fallisce se qualcuno introduce un import vietato in core/ — è il test che
protegge il vincolo esagonale nel tempo, non solo al momento della review.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = REPO_ROOT / "core"

# Allowlist = l'intera standard library dell'interprete (sys.stdlib_module_names,
# Python >= 3.10). Il template originale elencava a mano 14 moduli e vietava
# di fatto math/time/statistics/hashlib nel core: puri, ma non in lista.
# Restano vietati adapters/ e QUALSIASI pacchetto di terze parti.
_ALLOWED_EXTERNAL_PREFIXES = tuple(sorted(sys.stdlib_module_names))


def _imports_in(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def test_core_does_not_import_adapters():
    violations = []
    for path in CORE_DIR.rglob("*.py"):
        for module in _imports_in(path):
            if module.startswith("adapters"):
                violations.append(f"{path.relative_to(REPO_ROOT)} importa {module}")
    assert not violations, "core/ importa da adapters/, viola il confine esagonale:\n" + "\n".join(violations)


def test_core_does_not_import_unexpected_externals():
    violations = []
    for path in CORE_DIR.rglob("*.py"):
        for module in _imports_in(path):
            top = module.split(".")[0]
            if top == "core":
                continue
            # confronto ESATTO sul modulo di primo livello: con startswith()
            # 'requests' passava perché inizia con 're'.
            if top in _ALLOWED_EXTERNAL_PREFIXES:
                continue
            violations.append(f"{path.relative_to(REPO_ROOT)} importa {module}")
    assert not violations, "core/ importa pacchetti esterni non attesi:\n" + "\n".join(violations)


def test_guard_rejects_third_party_with_stdlib_like_prefix(tmp_path):
    """Regressione: 'requests' non deve passare perché inizia con 're'."""
    top = "requests".split(".")[0]
    assert top not in _ALLOWED_EXTERNAL_PREFIXES
    assert "re" in _ALLOWED_EXTERNAL_PREFIXES
