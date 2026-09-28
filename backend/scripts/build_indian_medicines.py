"""
Builds app/data/indian_medicines.tsv.gz from the Indian Medicine Dataset
(github.com/junioralive/Indian-Medicine-Dataset, MIT licence).

    python scripts/build_indian_medicines.py path/to/indian_medicine_data.csv

Keeps marketed products only, with brand, manufacturer, pack and composition.
Prices are dropped because they go stale.
"""
import csv
import gzip
import re
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "app" / "data" / "indian_medicines.tsv.gz"


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\t", " ")).strip()


def main(src: str) -> None:
    kept = 0
    with open(src, encoding="utf-8", newline="") as f, gzip.open(OUT, "wt", encoding="utf-8") as out:
        for row in csv.DictReader(f):
            if row["Is_discontinued"].strip().upper() != "FALSE" or row["type"].strip() != "allopathy":
                continue
            comp = " + ".join(c for c in (clean(row["short_composition1"]), clean(row["short_composition2"])) if c)
            if not comp:
                continue
            out.write("\t".join((clean(row["name"]), clean(row["manufacturer_name"]), clean(row["pack_size_label"]), comp)) + "\n")
            kept += 1
    print(f"{kept} products -> {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main(sys.argv[1])
