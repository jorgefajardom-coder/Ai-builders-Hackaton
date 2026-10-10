"""Instala un hook pre-commit que regenera site/ e incluye el resultado en cada commit.

Uso: python tools/install_hooks.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / ".git" / "hooks" / "pre-commit"

HOOK.write_text(
    "#!/bin/sh\n"
    "# Regenera la documentación HTML antes de cada commit (instalado por tools/install_hooks.py).\n"
    "python tools/build_docs.py >/dev/null || exit 1\n"
    "git add site/index.html site/version.json site/.nojekyll site/assets 2>/dev/null || git add site/index.html site/version.json site/.nojekyll\n",
    encoding="utf-8", newline="\n",
)
HOOK.chmod(0o755)
print(f"Hook instalado en {HOOK}")
