"""
Privacy: consent per purpose, guardian consent, legal documents, and who the user shares with.
"""
import html
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Optional
from app.core import privacy
from app.core.dependencies import require_user
from app.services.family_network import family_network_service

router = APIRouter()
LEGAL_DIR = Path(__file__).resolve().parents[3] / "legal"
DOCUMENTS = {
    "privacy-policy": "Privacy Policy",
    "terms": "Terms of Service",
    "medical-disclaimer": "Health Disclaimer",
}


class ConsentUpdate(BaseModel):
    choices: dict[str, bool]


@router.get("/consent/purposes")
async def consent_purposes():
    return {"policy_version": privacy.POLICY_VERSION, "adult_age": privacy.ADULT_AGE, "purposes": privacy.PURPOSES}


@router.get("/consent")
async def get_consent(user: dict = Depends(require_user)):
    return privacy.state(user["id"])


@router.put("/consent")
async def put_consent(body: ConsentUpdate, user: dict = Depends(require_user)):
    try:
        return privacy.update(user["id"], body.choices)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.get("/consent/history")
async def consent_history(user: dict = Depends(require_user)):
    record = dict.get(privacy._records, user["id"]) or {}
    return {"events": record.get("events", [])}


@router.post("/guardian/resend")
async def resend_guardian(user: dict = Depends(require_user)):
    return {"sent": await privacy.send_guardian_link(user["id"])}


def _page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        f"<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,"
        f"initial-scale=1'><title>{html.escape(title)}</title><style>body{{font:16px/1.5 system-ui,sans-serif;"
        f"max-width:40rem;margin:2rem auto;padding:0 1rem;color:#111;background:#fff}}label{{display:block;"
        f"margin:.75rem 0}}input[type=text]{{width:100%;padding:.5rem;font:inherit}}button{{font:inherit;"
        f"padding:.6rem 1rem;margin:.5rem .5rem 0 0}}small{{color:#555}}</style></head><body>"
        f"<h1>{html.escape(title)}</h1>{body}</body></html>"
    )


@router.get("/guardian/{token}", response_class=HTMLResponse)
async def guardian_form(token: str):
    link = privacy.guardian_link(token)
    if not link:
        return _page("Link expired", "<p>This link has expired or was already used. Ask the child to send a new one "
                                     "from the app.</p>")
    record = link["record"]
    requested = record.get("requested", {})
    boxes = []
    for pid, purpose in privacy.PURPOSES.items():
        if pid == "analytics":
            continue
        checked = " checked" if requested.get(pid) or purpose["required"] else ""
        boxes.append(f"<label><input type=checkbox name={pid} value=1{checked}> <b>{html.escape(purpose['title'])}"
                     f"</b>{' (required)' if purpose['required'] else ''}<br><small>{html.escape(purpose['detail'])}"
                     f"</small></label>")
    safe = html.escape(token, quote=True)
    return _page("Consent for a child's AdapFit account", f"""
<p>An AdapFit account was created with date of birth {html.escape(record.get('birth_date', ''))} and your email as
the parent or guardian. AdapFit tracks fitness and wellbeing; it does not diagnose or treat. Nothing is stored for
the child beyond the sign-up details until you agree. Product analytics is never used for children.</p>
<p>Read the <a href="../documents/privacy-policy">privacy policy</a> and <a href="../documents/terms">terms</a>.</p>
<form method=post action="{safe}">
<label>Your full name <input type=text name=name required maxlength=120></label>
<label>Relationship to the child <input type=text name=relationship required maxlength=60></label>
{''.join(boxes)}
<label><input type=checkbox name=declared_adult value=1 required> I am the child's parent or lawful guardian and I am
18 or over.</label>
<button name=decision value=agree>Agree</button>
<button name=decision value=decline formnovalidate>Decline and delete the account</button>
</form>""")


@router.post("/guardian/{token}", response_class=HTMLResponse)
async def guardian_submit(
    token: str, decision: str = Form(...), name: str = Form(""), relationship: str = Form(""),
    declared_adult: str = Form(""), health_data: str = Form(""), ai: str = Form(""), sharing: str = Form(""),
):
    try:
        if decision == "decline":
            await privacy.guardian_decline(token)
            return _page("Declined", "<p>The account and everything in it have been deleted.</p>")
        privacy.guardian_confirm(token, name, relationship, declared_adult == "1",
                                 {"health_data": health_data == "1", "ai": ai == "1", "sharing": sharing == "1"})
    except LookupError as exc:
        return _page("Link expired", f"<p>{html.escape(str(exc))}</p>")
    except ValueError as exc:
        return _page("Not saved", f"<p>{html.escape(str(exc))}</p><p><a href='{html.escape(token, quote=True)}'>"
                                  f"Back</a></p>")
    return _page("Thank you", "<p>Consent recorded. The child can now use the app. You can ask for the data to be "
                              "corrected or deleted at any time by writing to the grievance officer named in the "
                              "privacy policy.</p>")


@router.get("/documents")
async def list_documents():
    return {"version": privacy.POLICY_VERSION,
            "documents": [{"id": k, "title": v} for k, v in DOCUMENTS.items()]}


@router.get("/documents/{doc_id}", response_class=PlainTextResponse)
async def get_document(doc_id: str):
    if doc_id not in DOCUMENTS:
        raise HTTPException(status_code=404, detail="Unknown document")
    return (LEGAL_DIR / f"{doc_id}.md").read_text(encoding="utf-8")


class RevokeAccessRequest(BaseModel):
    entity_type: str
    entity_id: str
    data_types: Optional[list[str]] = None


@router.get("/overview")
async def get_privacy_overview(user: dict = Depends(require_user)):
    connections = family_network_service.get_connections(user["id"])
    shared_with = []
    for conn in connections:
        shared = [k for k, v in conn.get("i_share", {}).items() if v]
        shared_with.append({
            "user_id": conn["other_user_id"],
            "relationship": conn["relationship"],
            "data_shared": shared,
            "status": conn["status"],
            "connected_since": conn["connected_since"],
        })
    return {
        "user_id": user["id"],
        "total_connections": len(connections),
        "sharing_data_count": sum(1 for c in shared_with if c["data_shared"]),
        "shared_with": shared_with,
    }


@router.get("/access-history")
async def get_access_history(user: dict = Depends(require_user), limit: int = 50):
    return {"history": family_network_service.get_audit_history(user["id"], limit)}


@router.post("/revoke")
async def revoke_access(request: RevokeAccessRequest, user: dict = Depends(require_user)):
    if request.entity_type != "person":
        return {"error": f"Revocation for {request.entity_type} not implemented"}
    connections = family_network_service.get_connections(user["id"])
    for conn in connections:
        if conn["other_user_id"] == request.entity_id:
            if request.data_types:
                for dt in request.data_types:
                    family_network_service.revoke_permissions(conn["connection_id"], user["id"], dt)
                return {"revoked": True, "data_types": request.data_types}
            return family_network_service.revoke_connection(conn["connection_id"], user["id"])
    return {"error": "Connection not found"}


@router.get("/data-categories")
async def get_data_categories():
    return {"categories": [
        {"id": "activity", "name": "Activity", "sensitivity": "low"},
        {"id": "vitals", "name": "Vital Signs", "sensitivity": "high"},
        {"id": "sleep", "name": "Sleep", "sensitivity": "medium"},
        {"id": "nutrition", "name": "Nutrition", "sensitivity": "low"},
        {"id": "mental_health", "name": "Mental Health", "sensitivity": "high"},
        {"id": "medications", "name": "Medications", "sensitivity": "high"},
        {"id": "location", "name": "Location", "sensitivity": "high"},
        {"id": "medical", "name": "Medical Info", "sensitivity": "critical"},
    ]}


@router.get("/export")
async def get_export_options(user: dict = Depends(require_user)):
    return {"formats": ["json", "csv"], "everything": "/api/v1/export/all", "per_type": "/api/v1/export/formats"}
