"""Knowledge base SDLC su filesystem: docs, wiki, ADR, runbook, README del
repo + i documenti ingeriti da n8n (kb_dir) + la storia git come documento."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from core.ports import DocumentSourcePort


class FileSystemDocuments(DocumentSourcePort):
    def __init__(self, roots: list[str | Path], kb_dir: str | Path, git_repo: str | Path | None = None,
                 patterns: tuple[str, ...] = ("*.md",), base: str | Path | None = None,
                 git_log_limit: int = 200):
        self.roots = [Path(r) for r in roots]
        self.kb_dir = Path(kb_dir)
        self.git_repo = Path(git_repo) if git_repo else None
        self.patterns, self.git_log_limit = patterns, git_log_limit
        self.base = Path(base) if base else None

    def _rel(self, p: Path) -> str:
        if self.base:
            try:
                return str(p.resolve().relative_to(self.base.resolve()))
            except ValueError:
                pass
        return str(p)

    def documents(self):
        seen = set()
        for root in [*self.roots, self.kb_dir]:
            files = [root] if root.is_file() else [f for pat in self.patterns for f in root.rglob(pat)] if root.exists() else []
            for f in sorted(files):
                if f.resolve() in seen:
                    continue
                seen.add(f.resolve())
                yield self._rel(f), f.read_text(encoding="utf-8", errors="replace")
        if self.git_repo is not None:
            log = self._git_log()
            if log:
                yield "git-log", log

    def _git_log(self) -> str:
        try:
            out = subprocess.run(["git", "-C", str(self.git_repo), "log", f"-{self.git_log_limit}",
                                  "--date=short", "--pretty=format:%ad %h %s%n%n%b"],
                                 capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            return ""
        if out.returncode != 0:
            return ""
        return "# Storia del repository (git log)\n\n" + re.sub(r"\n{3,}", "\n\n", out.stdout)

    def add(self, name, text):
        safe = re.sub(r"[^\w.\-]", "_", Path(name).name) or "documento.md"
        if not safe.endswith(".md"):
            safe += ".md"
        self.kb_dir.mkdir(parents=True, exist_ok=True)
        dest = self.kb_dir / safe
        dest.write_text(text, encoding="utf-8")
        return self._rel(dest)
