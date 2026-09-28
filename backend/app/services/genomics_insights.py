"""
Genomics: reads a consumer DNA raw-data file (23andMe or AncestryDNA) and
reports a fixed panel of well-studied variants.

Nothing here is a personal risk. Associations are shown as the published
per-copy odds ratio with its source, which describes study populations and not
the user. Pharmacogenomic phenotypes follow CPIC allele definitions and end in
"tell your prescriber", never a dose. Only the panel genotypes are kept; the
raw file is discarded after parsing.
"""
import io
import time
import zipfile
from typing import Iterable, Optional

MAX_UPLOAD_BYTES = 60 * 1024 * 1024

CHIP_CAVEAT = (
    "Consumer DNA chips misread some variants, rare ones most of all. Confirm any result with a "
    "clinical-grade test before a doctor acts on it."
)
ANCESTRY_CAVEAT = (
    "Most of these studies were done in people of European ancestry; the effect in Indian "
    "populations may be larger, smaller or unmeasured."
)

# rsid -> (effect allele on the + strand, as the chip reports it)
ASSOCIATIONS = [
    {
        "id": "tcf7l2", "gene": "TCF7L2", "rsid": "rs7903146", "effect_allele": "T",
        "condition": "Type 2 diabetes", "odds_ratio_per_copy": 1.4,
        "source": "Tong et al., BMC Medical Genetics 2009 (meta-analysis, including South Asian cohorts)",
        "what_helps": "Regular activity, weight in a healthy range and periodic fasting glucose or HbA1c checks lower type 2 diabetes risk for every genotype.",
    },
    {
        "id": "fto", "gene": "FTO", "rsid": "rs9939609", "effect_allele": "A",
        "condition": "Obesity", "odds_ratio_per_copy": 1.31,
        "source": "Frayling et al., Science 2007",
        "what_helps": "Studies find physical activity reduces this variant's effect on weight by roughly a third or more.",
    },
    {
        "id": "9p21", "gene": "9p21 (CDKN2B-AS1)", "rsid": "rs10757278", "effect_allele": "G",
        "condition": "Coronary artery disease", "odds_ratio_per_copy": 1.29,
        "source": "Helgadottir et al., Science 2007",
        "what_helps": "Blood pressure, cholesterol, not smoking and activity matter far more than this variant; a doctor can check the first two.",
    },
    {
        "id": "9p21b", "gene": "9p21 (CDKN2B-AS1)", "rsid": "rs1333049", "effect_allele": "C",
        "condition": "Coronary artery disease", "odds_ratio_per_copy": 1.36,
        "source": "Samani et al., NEJM 2007",
        "what_helps": "Blood pressure, cholesterol, not smoking and activity matter far more than this variant; a doctor can check the first two.",
    },
]

# Shown only after the user asks to see them: no prevention changes the
# result, and guidelines advise counselling before disclosure.
APOE = {
    "id": "apoe", "gene": "APOE", "rsids": ("rs429358", "rs7412"),
    "condition": "Alzheimer's disease",
    "odds_ratios": {"e2/e4": 2.6, "e3/e4": 3.2, "e4/e4": 14.9},
    "source": "Farrer et al., JAMA 1997 (white clinical and population samples)",
    "counselling": "Talk to a genetic counsellor before or after viewing this. Many people with e4 never develop Alzheimer's, and many without it do.",
}

TRAITS = [
    {"id": "lct", "gene": "LCT/MCM6", "rsid": "rs4988235", "effect_allele": "A", "trait": "Lactase persistence",
     "copies_meaning": {0: "Likely lactose intolerant as an adult", 1: "Likely digests lactose", 2: "Likely digests lactose"}},
    {"id": "actn3", "gene": "ACTN3", "rsid": "rs1815739", "effect_allele": "T", "trait": "Fast-twitch muscle protein (R577X)",
     "copies_meaning": {0: "RR: both copies make alpha-actinin-3, common in sprint athletes",
                        1: "RX: one working copy", 2: "XX: no alpha-actinin-3; slightly more common in endurance athletes"}},
    {"id": "aldh2", "gene": "ALDH2", "rsid": "rs671", "effect_allele": "A", "trait": "Alcohol flush",
     "copies_meaning": {0: "Typical alcohol breakdown", 1: "Flushing after alcohol likely; the acetaldehyde build-up is harmful",
                        2: "Strong flushing likely; alcohol is best avoided"}},
    {"id": "mthfr", "gene": "MTHFR", "rsid": "rs1801133", "effect_allele": "A", "trait": "MTHFR C677T",
     "copies_meaning": {0: "No C677T copies", 1: "One C677T copy, very common",
                        2: "Two C677T copies; about 10% of people. Guidelines advise no special supplement for this result alone"}},
]

# CPIC allele-defining SNPs on the + strand.
CYP2C19 = {"no_function": {"rs4244285": "A", "rs4986893": "A"}, "increased": {"rs12248560": "T"}}
CYP2C9 = {"rs1799853": ("T", 0.5), "rs1057910": ("C", 0.0)}
SLCO1B1 = ("rs4149056", "C")
VKORC1 = ("rs9923231", "T")

PGX_DRUGS = {
    "CYP2C19": ["clopidogrel", "omeprazole", "pantoprazole", "esomeprazole", "lansoprazole", "citalopram",
                "escitalopram", "sertraline", "voriconazole", "amitriptyline"],
    "CYP2C9": ["warfarin", "phenytoin", "celecoxib", "ibuprofen", "meloxicam", "piroxicam"],
    "SLCO1B1": ["simvastatin", "atorvastatin", "rosuvastatin"],
    "VKORC1": ["warfarin", "acenocoumarol"],
}
PGX_NOTES = {
    "CYP2C19": "Can change how well clopidogrel, some acid reducers and some antidepressants work.",
    "CYP2C9": "Can change how quickly warfarin, phenytoin and some painkillers are cleared.",
    "SLCO1B1": "Can raise the chance of muscle side effects on some statins, simvastatin most.",
    "VKORC1": "Can change the warfarin dose a doctor starts with.",
}
NOT_CALLABLE = {
    "CYP2D6": "Needs copy-number testing that DNA chips cannot do; ask for a clinical test if a prescriber needs it.",
}

PANEL_RSIDS = (
    {a["rsid"] for a in ASSOCIATIONS} | set(APOE["rsids"]) | {t["rsid"] for t in TRAITS}
    | set(CYP2C19["no_function"]) | set(CYP2C19["increased"]) | set(CYP2C9) | {SLCO1B1[0], VKORC1[0]}
)


def _text_lines(data: bytes) -> Iterable[str]:
    if data[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            name = next((n for n in zf.namelist() if n.lower().endswith(".txt")), None)
            if name is None:
                return []
            data = zf.read(name)
    return data.decode("utf-8", errors="replace").splitlines()


def parse_raw_file(data: bytes) -> dict[str, str]:
    """rsid -> two-letter genotype for panel SNPs; handles 23andMe and AncestryDNA layouts."""
    out: dict[str, str] = {}
    for line in _text_lines(data):
        if not line or line[0] == "#" or not line.startswith("rs"):
            continue
        cols = line.replace(",", "\t").split()
        if cols[0] not in PANEL_RSIDS:
            continue
        geno = "".join(cols[3:5]) if len(cols) >= 5 else (cols[3] if len(cols) == 4 else "")
        geno = geno.upper()
        if len(geno) == 2 and set(geno) <= set("ACGT"):
            out[cols[0]] = geno
        elif len(geno) == 1 and geno in "ACGT":
            out[cols[0]] = geno * 2
    return out


def _copies(genotypes: dict, rsid: str, allele: str) -> Optional[int]:
    g = genotypes.get(rsid)
    return None if g is None else g.count(allele)


def _apoe(genotypes: dict) -> Optional[str]:
    a, b = genotypes.get("rs429358"), genotypes.get("rs7412")
    if not a or not b:
        return None
    c4, t2 = a.count("C"), b.count("T")
    if c4 + t2 > 2:
        return None
    alleles = ["e4"] * c4 + ["e2"] * t2
    alleles += ["e3"] * (2 - len(alleles))
    return "/".join(sorted(alleles))


def _cyp2c19(g: dict) -> Optional[dict]:
    tested = [r for r in (*CYP2C19["no_function"], *CYP2C19["increased"]) if r in g]
    if "rs4244285" not in g:
        return None
    nf = sum(_copies(g, r, a) or 0 for r, a in CYP2C19["no_function"].items())
    inc = _copies(g, "rs12248560", "T") or 0
    if nf >= 2:
        pheno = "Poor metabolizer"
    elif nf == 1:
        pheno = "Intermediate metabolizer"
    elif inc == 2:
        pheno = "Ultrarapid metabolizer"
    elif inc == 1:
        pheno = "Rapid metabolizer"
    else:
        pheno = "Normal metabolizer"
    return {"phenotype": pheno, "snps_read": tested}


def _cyp2c9(g: dict) -> Optional[dict]:
    if not all(r in g for r in CYP2C9):
        return None
    score = 2.0
    for rsid, (allele, value) in CYP2C9.items():
        score -= (_copies(g, rsid, allele) or 0) * (1 - value)
    score = max(score, 0.0)
    pheno = "Normal metabolizer" if score >= 2 else "Intermediate metabolizer" if score >= 1 else "Poor metabolizer"
    return {"phenotype": pheno, "activity_score": score, "snps_read": list(CYP2C9)}


def _single(g: dict, rsid: str, allele: str, labels: tuple[str, str, str]) -> Optional[dict]:
    n = _copies(g, rsid, allele)
    return None if n is None else {"phenotype": labels[n], "snps_read": [rsid]}


class GenomicsInsightsService:
    """Per-user panel result; the raw file is never stored."""

    def __init__(self):
        self.genotypes: dict[str, str] = {}
        self.uploaded_at: Optional[float] = None
        self.source_snps = 0
        self.show_apoe = False

    def upload(self, data: bytes) -> dict:
        if len(data) > MAX_UPLOAD_BYTES:
            return {"status": "too_large", "message": "That file is larger than any raw DNA export."}
        try:
            genotypes = parse_raw_file(data)
        except zipfile.BadZipFile:
            return {"status": "unreadable", "message": "The zip file could not be opened."}
        if not genotypes:
            return {"status": "unreadable",
                    "message": "No panel variants found. Upload the raw data file from 23andMe or AncestryDNA."}
        self.genotypes, self.uploaded_at, self.source_snps = genotypes, time.time(), len(genotypes)
        return self.report()

    def set_show_apoe(self, show: bool) -> dict:
        self.show_apoe = bool(show)
        return self.report()

    def forget(self) -> None:
        self.__init__()

    def report(self) -> dict:
        if not self.genotypes:
            return {"status": "no_data", "message": "No DNA file uploaded yet."}
        g = self.genotypes
        associations = []
        for a in ASSOCIATIONS:
            n = _copies(g, a["rsid"], a["effect_allele"])
            if n is None or any(x["gene"] == a["gene"] for x in associations):
                continue
            associations.append({**a, "genotype": g[a["rsid"]], "copies": n,
                                 "meaning": (f"You carry {n} cop{'y' if n == 1 else 'ies'} of the variant studied. "
                                             f"In studies, each copy was linked to about {a['odds_ratio_per_copy']}x "
                                             f"the odds of {a['condition'].lower()}, compared with people without it."
                                             if n else "You do not carry the variant studied.")})
        apoe_type = _apoe(g)
        apoe = None
        if apoe_type:
            apoe = {"available": True, "shown": self.show_apoe, "counselling": APOE["counselling"]}
            if self.show_apoe:
                apoe.update(genotype=apoe_type, condition=APOE["condition"], source=APOE["source"],
                            odds_ratio=APOE["odds_ratios"].get(apoe_type))

        traits = []
        for t in TRAITS:
            n = _copies(g, t["rsid"], t["effect_allele"])
            if n is not None:
                traits.append({"id": t["id"], "gene": t["gene"], "trait": t["trait"], "genotype": g[t["rsid"]],
                               "meaning": t["copies_meaning"][n]})

        pgx = {
            "CYP2C19": _cyp2c19(g),
            "CYP2C9": _cyp2c9(g),
            "SLCO1B1": _single(g, *SLCO1B1, ("Normal function", "Decreased function", "Poor function")),
            "VKORC1": _single(g, *VKORC1, ("Typical warfarin sensitivity", "Increased warfarin sensitivity",
                                            "High warfarin sensitivity")),
        }
        pharmacogenomics = []
        for gene, res in pgx.items():
            entry = {"gene": gene, "drugs": PGX_DRUGS[gene], "note": PGX_NOTES[gene]}
            if res is None:
                entry.update(phenotype=None, status="not_in_file")
            else:
                entry.update(res, status="read",
                             action=("Tell your prescriber and pharmacist about this result before starting any of "
                                     "these medicines. Do not change a medicine you already take."))
            pharmacogenomics.append(entry)
        for gene, why in NOT_CALLABLE.items():
            pharmacogenomics.append({"gene": gene, "status": "not_callable", "phenotype": None, "note": why})

        return {
            "status": "ok", "uploaded_at": self.uploaded_at, "variants_read": self.source_snps,
            "associations": associations, "apoe": apoe, "traits": traits, "pharmacogenomics": pharmacogenomics,
            "caveats": [CHIP_CAVEAT, ANCESTRY_CAVEAT,
                        "An odds ratio describes groups in a study, not your chance of getting a condition."],
            "next_step": "Discuss any result you plan to act on with a doctor or genetic counsellor.",
        }

    def check_drugs(self, medications: list[str]) -> dict:
        report = self.report()
        if report["status"] != "ok":
            return {"status": "no_data", "results": []}
        wanted = {m.strip().lower() for m in medications if m.strip()}
        results = []
        for entry in report["pharmacogenomics"]:
            if entry["status"] != "read":
                continue
            for drug in wanted & set(entry["drugs"]):
                if entry["phenotype"] not in ("Normal metabolizer", "Normal function", "Typical warfarin sensitivity"):
                    results.append({"drug": drug, "gene": entry["gene"], "phenotype": entry["phenotype"],
                                    "message": f"{entry['note']} Tell your prescriber you are a {entry['phenotype'].lower()} for {entry['gene']}.",
                                    "action": entry["action"]})
        return {"status": "ok", "results": results,
                "note": "No result means none of your listed medicines is affected by the genes read from your file."}


from app.core.per_user import per_user, register  # noqa: E402

genomics_insights_service = register("genomics.genomics_insights_service", per_user(GenomicsInsightsService))
