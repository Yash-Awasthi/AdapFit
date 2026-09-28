"""
Check a forward: paste a health message (often a WhatsApp forward) and get a
plain-language verdict with who to trust. The model may only point to named
public-health bodies; with no model available the answer is "unverified".
"""
import json
import re
from typing import Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.safety_policy import SAFETY_RULES, triage

router = APIRouter()

TRUSTED = ["WHO", "ICMR", "Ministry of Health and Family Welfare (MoHFW)", "FSSAI", "AIIMS", "PIB Fact Check", "NHS", "CDC"]
PROMPT = f"""You check health claims that circulate in India, often as WhatsApp forwards.
Reply with JSON only: {{"verdict": "supported|misleading|false|unproven", "explanation": "2-3 plain sentences",
"what_to_do": "one safe, practical sentence", "sources": ["organisation names"]}}.
Use only these organisations as sources: {", ".join(TRUSTED)}. Never invent a study, statistic or link.
If the evidence is unclear, say "unproven". Never tell anyone to stop, start or change a medicine.
{SAFETY_RULES}"""

UNVERIFIED = {
    "verdict": "unverified",
    "explanation": "This could not be checked automatically right now.",
    "what_to_do": "Search the claim on factcheck.pib.gov.in or ask a doctor before acting on it or forwarding it.",
    "sources": ["PIB Fact Check"],
}


class ForwardCheck(BaseModel):
    text: str = Field(min_length=10, max_length=4000)


class Verdict(BaseModel):
    verdict: Literal["supported", "misleading", "false", "unproven", "unverified"]
    explanation: str
    what_to_do: str
    sources: list[str]
    safety: Optional[dict] = None


def _parse(reply: str) -> Optional[dict]:
    m = re.search(r"\{.*\}", reply or "", re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
        data["sources"] = [s for s in data.get("sources", []) if any(t.split(" (")[0] in s for t in TRUSTED)]
        return Verdict(**data).model_dump()
    except (ValueError, TypeError):
        return None


@router.post("/check", response_model=Verdict)
async def check_forward(req: ForwardCheck):
    flagged = triage(req.text)
    if flagged:
        return {**UNVERIFIED, "explanation": flagged["reply"], "safety": flagged}
    from app.api.v1.endpoints.chat import _call_gemini, _call_groq

    prompt = f"Claim to check:\n\"\"\"{req.text}\"\"\""
    reply = await _call_gemini(prompt, [], system=PROMPT) or await _call_groq(prompt, system=PROMPT)
    return _parse(reply) or UNVERIFIED
