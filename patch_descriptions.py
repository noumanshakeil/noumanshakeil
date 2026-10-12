"""Push curated descriptions to GitHub for repos with empty/weak descriptions."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from descriptions import DESCRIPTIONS, SKIP, SKIP_PREFIXES

ROOT = Path(__file__).parent
public = {r["name"]: r for r in json.loads((ROOT / "repos.json").read_text(encoding="utf-8"))}


def weak(desc: str) -> bool:
    d = (desc or "").strip()
    if not d:
        return True
    low = d.lower()
    return low.startswith("hands-on project") or low in {"capstone project"}


patched = 0
skipped = 0
for name, text in DESCRIPTIONS.items():
    if name in SKIP or any(name.startswith(p) for p in SKIP_PREFIXES):
        continue
    if name not in public:
        continue  # don't PATCH private via this path unless present
    current = public[name].get("description") or ""
    if not weak(current) and current.strip() == text.strip():
        skipped += 1
        continue
    # Always update if weak; also update if curated is clearly better and current is short/generic
    if not weak(current) and len(current) > 40:
        skipped += 1
        continue
    body = {"description": text[:350]}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(body, f)
        path = f.name
    try:
        subprocess.check_call(
            ["gh", "api", "-X", "PATCH", f"repos/noumanshakeil/{name}", "--input", path],
            stdout=subprocess.DEVNULL,
        )
        print(f"patched {name}")
        patched += 1
    except subprocess.CalledProcessError as e:
        print(f"FAIL {name}: {e}")
    finally:
        Path(path).unlink(missing_ok=True)

print(f"Done. patched={patched} skipped={skipped}")
