"""
Build app/data/cdsco_prohibited_fdc.tsv: fixed dose combinations prohibited under
Section 26A of the Drugs and Cosmetics Act 1940, from government sources only.

    python -m scripts.build_cdsco_fdc

Sources (downloaded each run, never edited by hand):
  1. CDSCO, "List of drugs prohibited for manufacture and sale through gazette
     notifications ... present status as on 22.11.2021", with its footnotes on
     notifications under Supreme Court review or quashed by the Delhi High Court.
  2. Lok Sabha unstarred question 2632, 04.08.2023, Annexure A: 14 FDCs,
     S.O. 2394(E) to 2407(E) dated 02.06.2023.
  3. Directorate of Food and Drugs Administration, Goa: 156 FDCs, S.O. 3285(E)
     to 3440(E) dated 02.08.2024.
  4. PIB release 2275595, 20.06.2026: 16 FDCs (e-Gazette 273649).

PDF text extraction breaks some words; a broken name only fails to match.
"""
import io
import re
import urllib.request
from pathlib import Path

import pypdf

OUT = Path(__file__).resolve().parent.parent / "app" / "data" / "cdsco_prohibited_fdc.tsv"
CDSCO = ("https://cdsco.gov.in/opencms/resources/UploadCDSCOWeb/2018/UploadConsumer/"
         "Updated%20Banned%20Drugs%20List%20(1).pdf")
LOK_SABHA = "https://sansad.in/getFile/loksabhaquestions/annex/1712/AU2632.pdf?source=pqals"
GOA = "https://www.goa.gov.in/wp-content/uploads/2024/08/FDC-DRUGS-BANNED.pdf"
PIB = "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2275595"

# CDSCO footnotes. 1#: stayed by the Madras High Court. 3# and 4#: claimed as marketed
# before 1988, back with the expert committee.
# 5#: the notification was quashed by the Delhi High Court and the appeal is pending.
STATUS = {"1": "stayed", "3": "under_review", "4": "under_review", "5": "quashed"}

PIB_2026 = [
    "Acetyl Salicylic acid + Ethoheptazine",
    "Aloe Extract + Allantoin + Alphatocopherol Acetate + D-Penthenol + Vitamin A",
    "Aloe Extract + Vitamin E + Dimethicone + Glycerine",
    "Aloe Vera + Jojoba Oil + Vitamin E",
    "Aloe vera + Orange oil",
    "Aloe vera + Jojoba oil + Wheat germ oil + Tea tree oil",
    "Aloe vera + Vitamin E + Herbal",
    "Dicyclomine + Paracetamol + Clidinium Bromide",
    "Dicyclomine + Paracetamol + Clidinium Bromide + Chlordiazepoxide",
    "Gliclazide + Chromium Picolinate",
    "Paracetamol + Lignocaine",
    "Amoxicillin + Serratiopeptidase + Lactobacillus Sporogenes",
    "Amoxicillin + Cloxacillin + Lactic acid bacillus + Serratiopeptidase",
    "Amoxicillin + Serratiopeptidase",
    "Cefadroxyl + Probenecid",
    "Cefuroxime + Serratiopeptidase",
]


def _pdf_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=60).read()
    return "\n".join(page.extract_text() or "" for page in pypdf.PdfReader(io.BytesIO(data)).pages)


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip(" .")


def cdsco_2021(text: str):
    body = text.split("Sr. No.", 1)[1]
    body = body.replace("1# Presently stayed by the Hon’ble High Court of Madras.", "")
    body = body[:body.rfind("\n2#")]  # the footnotes that close the list
    for chunk in re.split(r"\n\s*(?=\d{1,3}\.\s)", "\n" + body):
        # "95.  3# Name" and, once, "118. 1 5# Name": a stray digit before the footnote marker.
        m = re.match(r"\s*(\d{1,3})\.\s*(?:\d\s+(?=\d#))?(?:(\d)#)?(.*)", chunk, re.S)
        if not m:
            continue
        rest = m.group(3)
        split = re.search(r"S\.\s?O\.|G\.?\s?S\.?\s?R", rest)
        name = _clean(rest[:split.start()] if split else rest)
        note = _clean(rest[split.start():]) if split else ""
        marker = m.group(2) or (re.match(r"\s*(\d)#", rest) or [None, None])[1]
        name = re.sub(r"^\d#\s*", "", name)
        if "+" in name:
            yield name, note, STATUS.get(marker, "prohibited"), "CDSCO list as on 22.11.2021"


def lok_sabha_2023(text: str):
    annex = text.split("Annexure", 1)[1]
    for m in re.finditer(r"\n\s*\d{1,2}\.\s(.+?)(?=\n\s*\d{1,2}\.\s|\Z)", annex, re.S):
        name = _clean(re.sub(r"\(\d.*", "", m.group(1)))
        yield name, "S.O. 2394(E) to 2407(E) dated 02.06.2023", "prohibited", "Lok Sabha USQ 2632, 04.08.2023"


def goa_2024(text: str):
    text = re.sub(r"Page \d of \d", "", text)
    body = text.split("DATE", 1)[1]
    start = 0
    for m in re.finditer(r"S\.\s?O\.\s?(\d{4})\s?\(E\)\s*(\d{2}\.\d{2}\.\d{4})", body):
        name = _clean(re.sub(r"^\s*\d{1,3}\s", "", body[start:m.start()].strip()))
        start = m.end()
        if "+" in name:
            yield name, f"S.O. {m.group(1)}(E) dated {m.group(2)}", "prohibited", "Goa FDA list of 02.08.2024"


def main() -> None:
    rows = list(cdsco_2021(_pdf_text(CDSCO)))
    rows += lok_sabha_2023(_pdf_text(LOK_SABHA))
    rows += goa_2024(_pdf_text(GOA))
    rows += [(n, "Notifications of 20.06.2026, e-Gazette 273649", "prohibited", "PIB release 2275595")
             for n in PIB_2026]
    with OUT.open("w", encoding="utf-8") as f:
        f.write("combination\tnotification\tstatus\tsource\n")
        for row in rows:
            f.write("\t".join(c.replace("\t", " ") for c in row) + "\n")
    print(f"{len(rows)} combinations written to {OUT}")


if __name__ == "__main__":
    main()
