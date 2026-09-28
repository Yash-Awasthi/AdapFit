"""
Indian brand-name medicines and their compositions.

Data: the Indian Medicine Dataset (github.com/junioralive/Indian-Medicine-Dataset,
MIT licence), about 246,000 marketed allopathic products, built into
app/data/indian_medicines.tsv.gz by scripts/build_indian_medicines.py. It is
scraped retail data, not the CDSCO register, so results say "check the strip".
"""
import bisect
import gzip
import re
import sys
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "indian_medicines.tsv.gz"
SOURCE = "Indian Medicine Dataset (retail listings). Check the name and strength on your strip or with your pharmacist."

_STRENGTH = re.compile(r"\s*\([^)]*\)")


@lru_cache(maxsize=1)
def _index() -> tuple[list[str], list[tuple[str, str, str, str]]]:
    """Rows sorted by lowercase brand, with repeated strings interned; loaded on first use (~40 MB)."""
    rows = []
    with gzip.open(DATA, "rt", encoding="utf-8") as f:
        for line in f:
            brand, maker, pack, comp = line.rstrip("\n").split("\t")
            rows.append((brand, sys.intern(maker), sys.intern(pack), sys.intern(comp)))
    rows.sort(key=lambda r: r[0].lower())
    return [r[0].lower() for r in rows], rows


def generics(composition: str) -> list[str]:
    """'Amoxycillin (500mg) + Clavulanic Acid (125mg)' -> ['amoxycillin', 'clavulanic acid']."""
    return [_STRENGTH.sub("", part).strip().lower() for part in composition.split("+") if part.strip()]


def search(query: str, limit: int = 20) -> list[dict]:
    q = " ".join(query.lower().split())
    if len(q) < 2:
        return []
    keys, rows = _index()
    start = bisect.bisect_left(keys, q)
    out = []
    for i in range(start, min(start + 2000, len(keys))):
        if not keys[i].startswith(q):
            break
        brand, maker, pack, comp = rows[i]
        out.append({"brand": brand, "manufacturer": maker, "pack": pack, "composition": comp,
                    "generics": generics(comp)})
        if len(out) >= limit:
            break
    return out


def resolve(name: str) -> dict:
    """
    Generic ingredients for a name the user typed. An exact product name gives
    its composition. A bare brand gives what every product under it shares
    ('Crocin' is paracetamol); when they share nothing it is ambiguous and
    returns every ingredient, since a missed interaction is worse than an extra one.
    """
    q = " ".join(name.lower().split())
    matches = [m for m in search(q, limit=200)
               if m["brand"].lower() == q or m["brand"].lower().startswith(q + " ")]
    if not matches:
        return {"name": name, "kind": "unknown", "generics": [q]}
    exact = [m for m in matches if m["brand"].lower() == q]
    if exact:
        return {"name": name, "kind": "product", "generics": exact[0]["generics"], "composition": exact[0]["composition"]}
    shared = set(matches[0]["generics"])
    for m in matches[1:]:
        shared &= set(m["generics"])
    if shared:
        return {"name": name, "kind": "brand", "generics": sorted(shared), "products": len(matches)}
    return {"name": name, "kind": "ambiguous", "generics": sorted({g for m in matches for g in m["generics"]}),
            "options": sorted({m["composition"] for m in matches})[:10],
            "message": f"'{name}' covers products with different ingredients. Pick the exact product for a precise check."}
