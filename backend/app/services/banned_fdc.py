"""
Fixed dose combinations prohibited in India under Section 26A of the Drugs and
Cosmetics Act 1940, matched against a product's composition.

Data: app/data/cdsco_prohibited_fdc.tsv, built by scripts/build_cdsco_fdc.py
from the CDSCO list (status as on 22.11.2021), Lok Sabha USQ 2632 (2023), the
Goa FDA list of the 2024 notifications and PIB release 2275595 (2026).
A product matches when its ingredients are exactly a listed combination's and,
where the listing names a form (SR, injection, suspension, dispersible...), the
product's name shows that form. Listings tied to particular strengths are not
matched, since the retail data cannot confirm them. No match is not proof a
product is permitted: names in the source PDFs are sometimes broken by text
extraction, and category bans ("corticosteroids with any other drug") are not
matched by ingredient.
"""
import csv
import re
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

DATA = Path(__file__).resolve().parent.parent / "data" / "cdsco_prohibited_fdc.tsv"

# Salt, form and packaging words that do not change which active ingredient is meant.
_NOISE = re.compile(
    r"\b(hcl|hydrochloride|sodium|potassium|maleate|phosphate|citrate|sulphate|sulfate|bromide|"
    r"acetate|dihydrate|trihydrate|monohydrate|magnesium|calcium|bp|ip|usp|eq\.?|to|as|sr|"
    r"dispersible|tablets?|syrup|injection|suspension|capsules?|cream|gel|drops|"
    r"for human use|fixed dose combinations? of|and its formulations)\b"
)
_SPELLING = {
    "amoxycillin": "amoxicillin", "guaiphenesin": "guaifenesin", "chlopheniramine": "chlorpheniramine",
    "acetaminophen": "paracetamol", "lignocain": "lignocaine", "lidocaine": "lignocaine",
    "chloramphennicol": "chloramphenicol", "cefadroxyl": "cefadroxil",
    "dextromethophan": "dextromethorphan", "phenobarbitone": "phenobarbital",
}
_FORMS = {
    "sr": r"\b(sr|sustained|er|extended)\b", "injection": r"\binj(ection)?\b",
    "suspension": r"suspension", "syrup": r"syrup", "dispersible": r"dispersible|\bdt\b",
    "cream": r"cream", "gel": r"\bgel\b", "drops": r"drops", "ointment": r"ointment",
    "lotion": r"lotion", "kit": r"\bkit\b",
}
_STATUS_TEXT = {
    "prohibited": "is on the Government of India's list of prohibited fixed dose combinations",
    "under_review": "was prohibited in 2016; after a Supreme Court order it is back under expert review",
    "quashed": "was prohibited in 2018, but the Delhi High Court quashed that notification (appeal pending)",
    "stayed": "is prohibited, but the ban is stayed by the Madras High Court",
}


def _ingredient(name: str) -> str:
    n = re.sub(r"\([^)]*\)|\d+(\.\d+)?\s*(mg|mcg|g|ml|%|iu)\b", " ", name.lower())
    n = " ".join(_NOISE.sub(" ", n).split())
    # An ingredient that is all salt words ("sodium citrate") stays itself, never vanishes from the set.
    return _SPELLING.get(n, n) or " ".join(name.lower().split())


def _forms(text: str) -> frozenset:
    t = text.lower()
    return frozenset(f for f, rx in _FORMS.items() if re.search(rx, t))


def _key(ingredients) -> frozenset:
    return frozenset(i for i in (_ingredient(x) for x in ingredients) if i)


@lru_cache(maxsize=1)
def _index() -> dict:
    out: dict = {}
    with DATA.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            name = row["combination"]
            if re.search(r"\d\s*(mg|mcg|ml)\b", name, re.I):
                continue
            key = _key(name.split("+"))
            if len(key) >= 2:
                out.setdefault(key, []).append({**row, "forms": _forms(name)})
    return out


def check(generics: List[str], product_name: str = "") -> Optional[dict]:
    """The listing for exactly this combination (and form), the one in force first; None when not listed."""
    have = _forms(product_name)
    rows = [r for r in _index().get(_key(generics), []) if r["forms"] <= have]
    if not rows:
        return None
    row = sorted(rows, key=lambda r: r["status"] != "prohibited")[0]
    return {
        "status": row["status"],
        "message": f"This combination {_STATUS_TEXT[row['status']]} ({row['notification']}). "
                   "Do not stop a prescribed medicine on your own: ask your doctor or pharmacist about an alternative.",
        "notification": row["notification"],
        "source": row["source"],
    }
