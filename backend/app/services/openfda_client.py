"""OpenFDA API client — drug info, recalls, adverse events, food, devices.

Extracted from inspiration/ZFIT/openfda-mcp-server.
Pattern: query FDA open data API for drug safety, adverse events, recalls.
Provides structured access to FDA drug, device, food data.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any


OPENFDA_BASE = "https://api.fda.gov"


@dataclass
class DrugInfo:
    brand_name: str | None
    generic_name: str | None
    manufacturer: str | None
    product_type: str | None
    route: list[str] = field(default_factory=list)
    purpose: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    active_ingredients: list[dict] = field(default_factory=list)
    inactive_ingredients: list[dict] = field(default_factory=list)


@dataclass
class AdverseEvent:
    safety_report_id: str
    received_date: str | None
    drug_names: list[str]
    reactions: list[str]
    outcomes: list[str]
    patient_age: int | None
    patient_sex: str | None
    seriousness: str | None


@dataclass
class DrugRecall:
    recall_number: str
    product_description: str
    reason: str
    classification: str
    status: str
    date: str


# Indian (INN/BAN) names that differ from the US names openFDA indexes.
US_NAMES = {
    "paracetamol": "acetaminophen", "salbutamol": "albuterol", "adrenaline": "epinephrine",
    "noradrenaline": "norepinephrine", "glibenclamide": "glyburide", "frusemide": "furosemide",
    "lignocaine": "lidocaine", "pethidine": "meperidine", "orciprenaline": "metaproterenol",
    "thyroxine": "levothyroxine", "rifampicin": "rifampin", "cyclosporin": "cyclosporine",
}


def us_name(drug_name: str) -> str:
    key = drug_name.strip().lower()
    return US_NAMES.get(key, key)


def _fda_request(endpoint: str, params: dict, api_key: str | None = None) -> dict:
    """Make an OpenFDA API request."""
    url = f"{OPENFDA_BASE}/{endpoint}.json?{urllib.parse.urlencode(params)}"
    if api_key:
        url += f"&api_key={api_key}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"results": [], "error": "Not found"}
        return {"results": [], "error": str(e)}
    except Exception as e:
        return {"results": [], "error": str(e)}


def search_drug_label(drug_name: str, api_key: str | None = None) -> list[DrugInfo]:
    """Search FDA drug labeling information.

    https://api.fda.gov/drug/label.json?search=openfda.brand_name:"aspirin"
    """
    name = us_name(drug_name)
    params = {
        "search": f'openfda.brand_name:"{name}"+openfda.generic_name:"{name}"',
        "limit": "5",
    }
    data = _fda_request("drug/label", params, api_key)
    results = []
    for r in data.get("results", []):
        oa = r.get("openfda", {})
        results.append(DrugInfo(
            brand_name=oa.get("brand_name", [None])[0] if oa else None,
            generic_name=oa.get("generic_name", [None])[0] if oa else None,
            manufacturer=oa.get("manufacturer_name", [None])[0] if oa else None,
            product_type=oa.get("product_type", [None])[0] if oa else None,
            route=r.get("route", []),
            purpose=r.get("purpose", []),
            warnings=r.get("warnings", []),
            active_ingredients=r.get("active_ingredient", []),
            inactive_ingredients=r.get("inactive_ingredient", []),
        ))
    return results


def search_adverse_events(
    drug_name: str,
    limit: int = 50,
    api_key: str | None = None,
) -> list[AdverseEvent]:
    """Search FDA adverse event reports for a drug.

    https://api.fda.gov/drug/event.json?search=patient.drug.medicinalproduct:"aspirin"
    """
    params = {
        "search": f'patient.drug.medicinalproduct:"{drug_name}"',
        "limit": str(limit),
    }
    data = _fda_request("drug/event", params, api_key)
    results = []
    for r in data.get("results", []):
        patient = r.get("patient", {})
        drugs = patient.get("drug", [])
        reactions = patient.get("reaction", [])

        results.append(AdverseEvent(
            safety_report_id=r.get("safetyreportid", ""),
            received_date=r.get("receivedate", None),
            drug_names=[d.get("medicinalproduct", "") for d in drugs],
            reactions=[re.get("reactionmeddrapt", "") for re in reactions],
            outcomes=[d.get("actiondrug", "") for d in drugs],
            patient_age=int(patient.get("patientonsetage", 0)) if patient.get("patientonsetage") else None,
            patient_sex=patient.get("patientsex", None),
            seriousness=r.get("serious", None),
        ))
    return results


def search_drug_recalls(
    drug_name: str = "",
    limit: int = 50,
    api_key: str | None = None,
) -> list[DrugRecall]:
    """Search FDA drug enforcement reports (recalls).

    https://api.fda.gov/drug/enforcement.json?search=...
    """
    search = f'product_description:"{drug_name}"' if drug_name else ""
    params = {"search": search, "limit": str(limit)} if search else {"limit": str(limit)}
    data = _fda_request("drug/enforcement", params, api_key)
    results = []
    for r in data.get("results", []):
        results.append(DrugRecall(
            recall_number=r.get("recall_number", ""),
            product_description=r.get("product_description", ""),
            reason=r.get("reason_for_recall", ""),
            classification=r.get("classification", ""),
            status=r.get("status", ""),
            date=r.get("recall_initiation_date", ""),
        ))
    return results


def get_drug_interactions(drug_name: str, api_key: str | None = None) -> dict:
    """Get drug interaction information from FDA data.

    Combines label warnings and adverse event reports.
    """
    labels = search_drug_label(drug_name, api_key)
    events = search_adverse_events(drug_name, 20, api_key)
    recalls = search_drug_recalls(drug_name, 10, api_key)

    all_warnings = []
    for label in labels:
        all_warnings.extend(label.warnings)

    common_reactions: dict[str, int] = {}
    for event in events:
        for reaction in event.reactions:
            common_reactions[reaction] = common_reactions.get(reaction, 0) + 1

    top_reactions = sorted(common_reactions.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "drug": drug_name,
        "warnings": all_warnings[:20],
        "common_reactions": top_reactions,
        "adverse_event_count": len(events),
        "recalls": [
            {"reason": r.reason, "classification": r.classification, "date": r.date}
            for r in recalls
        ],
    }
