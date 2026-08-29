"""
Health Misinformation Detection — Claim Verification & Source Credibility
Fact-checking health claims, source scoring, evidence-based responses
"""
from datetime import datetime
from typing import Dict, List
import random


class HealthMisinformationService:
    """Health claim verification and misinformation detection platform"""

    def __init__(self):
        self.credible_sources = {
            "tier_1": {
                "name": "Highest Evidence",
                "sources": ["WHO", "CDC", "NIH", "FDA", "Cochrane Library", "PubMed", "JAMA", "NEJM", "Lancet"],
                "credibility_score": 95,
            },
            "tier_2": {
                "name": "High Evidence",
                "sources": ["Mayo Clinic", "Cleveland Clinic", "Johns Hopkins", "Harvard Health", "WebMD (professional)", "UpToDate"],
                "credibility_score": 85,
            },
            "tier_3": {
                "name": "Moderate Evidence",
                "sources": ["Healthline", "Medical News Today", "Everyday Health", "Prevention Magazine"],
                "credibility_score": 70,
            },
            "tier_4": {
                "name": "Low Evidence",
                "sources": ["Social media posts", "Personal blogs", "YouTube videos", "TikTok health tips"],
                "credibility_score": 30,
            },
        }

        self.common_misinformation = {
            "detox_myths": {
                "claim": "You need to detox your body with special cleanses",
                "reality": "Your liver and kidneys naturally detoxify your body. No special cleanses are needed.",
                "evidence_level": "strong_against",
                "correct_sources": ["Mayo Clinic", "NIDDK"],
            },
            "superfood_hype": {
                "claim": "This single superfood will cure all your health problems",
                "reality": "No single food is a magic cure. Balanced nutrition from varied foods is key.",
                "evidence_level": "strong_against",
                "correct_sources": ["Academy of Nutrition and Dietetics"],
            },
            "vaccine_myths": {
                "claim": "Vaccines cause autism",
                "reality": "Extensive research has found no link between vaccines and autism. This myth originated from a retracted study.",
                "evidence_level": "strong_against",
                "correct_sources": ["CDC", "WHO", "AAP"],
            },
            "gmo_fears": {
                "claim": "GMO foods are dangerous to your health",
                "reality": "Scientific consensus from major health organizations confirms approved GMO foods are safe to eat.",
                "evidence_level": "strong_against",
                "correct_sources": ["WHO", "National Academies of Sciences"],
            },
            "alkaline_diet": {
                "claim": "Alkaline diets prevent cancer and disease",
                "reality": "Your body maintains its pH regardless of diet. No evidence supports alkaline diets for disease prevention.",
                "evidence_level": "moderate_against",
                "correct_sources": ["Cancer Research UK", "MD Anderson"],
            },
        }

        self.evidence_levels = {
            "strong_for": {"description": "Multiple high-quality studies support this claim", "score": 90},
            "moderate_for": {"description": "Some evidence supports this claim", "score": 70},
            "uncertain": {"description": "Insufficient evidence to confirm or deny", "score": 50},
            "moderate_against": {"description": "Some evidence contradicts this claim", "score": 30},
            "strong_against": {"description": "Strong evidence contradicts this claim", "score": 10},
        }

    def verify_claim(self, claim: str, source: str = None) -> Dict:
        """Verify a health claim against evidence"""
        claim_lower = claim.lower()

        # Check against known misinformation
        known_match = None
        for key, data in self.common_misinformation.items():
            keywords = key.replace("_", " ").split()
            if any(kw in claim_lower for kw in keywords):
                known_match = data
                break

        # Determine source credibility
        source_credibility = self._get_source_credibility(source) if source else {"score": 50, "tier": "unknown"}

        if known_match:
            return {
                "claim": claim,
                "verification": "misleading",
                "confidence": 0.92,
                "reality": known_match["reality"],
                "evidence_level": known_match["evidence_level"],
                "correct_sources": known_match["correct_sources"],
                "source_credibility": source_credibility,
                "recommendation": "This claim is not supported by scientific evidence. Consult trusted medical sources.",
            }

        # General claim analysis
        verification = self._analyze_claim(claim_lower)

        return {
            "claim": claim,
            "verification": verification["status"],
            "confidence": verification["confidence"],
            "summary": verification["summary"],
            "evidence_level": verification["evidence_level"],
            "recommended_sources": self._get_recommended_sources(claim_lower),
            "source_credibility": source_credibility,
            "recommendation": verification["recommendation"],
        }

    def _get_source_credibility(self, source: str) -> Dict:
        """Score source credibility"""
        source_lower = source.lower() if source else ""
        for tier_name, tier_data in self.credible_sources.items():
            for s in tier_data["sources"]:
                if s.lower() in source_lower:
                    return {"score": tier_data["credibility_score"], "tier": tier_name, "name": tier_data["name"]}
        return {"score": 40, "tier": "unverified", "name": "Unverified Source"}

    def _analyze_claim(self, claim: str) -> Dict:
        """Analyze a health claim"""
        # Red flags for misinformation
        red_flags = [
            "cures everything", "miracle", "secret they don't want", "big pharma",
            "natural always better", "ancient remedy", "suppressed research",
            "100% effective", "no side effects", "guaranteed results",
        ]

        has_red_flags = any(flag in claim for flag in red_flags)

        if has_red_flags:
            return {
                "status": "potentially_misleading",
                "confidence": 0.75,
                "summary": "This claim contains language commonly associated with health misinformation.",
                "evidence_level": "uncertain",
                "recommendation": "Verify this claim with trusted medical sources before acting on it.",
            }

        return {
            "status": "unverified",
            "confidence": 0.6,
            "summary": "This claim could not be definitively verified. More information needed.",
            "evidence_level": "uncertain",
            "recommendation": "Consult a healthcare professional for personalized advice.",
        }

    def _get_recommended_sources(self, claim: str) -> List[str]:
        """Get recommended sources for verification"""
        return ["PubMed", "Cochrane Library", "WHO", "CDC", "Mayo Clinic"]

    def score_article_credibility(self, article_data: Dict) -> Dict:
        """Score the credibility of a health article"""
        source = article_data.get("source", "")
        claims = article_data.get("claims", [])
        has_citations = article_data.get("has_citations", False)
        author_credentials = article_data.get("author_credentials", "")

        # Source score
        source_score = self._get_source_credibility(source)["score"]

        # Citation score
        citation_score = 80 if has_citations else 30

        # Author score
        author_score = 70 if any(cred in author_credentials.lower() for cred in ["md", "phd", "dr", "professor"]) else 40

        # Claims analysis
        claims_score = 60
        for claim in claims:
            verification = self.verify_claim(claim)
            if verification["verification"] == "misleading":
                claims_score -= 20

        overall_score = round((source_score * 0.3 + citation_score * 0.2 + author_score * 0.2 + max(0, claims_score) * 0.3), 1)

        return {
            "article_title": article_data.get("title", "Unknown"),
            "overall_credibility": overall_score,
            "breakdown": {
                "source_credibility": source_score,
                "citation_quality": citation_score,
                "author_credentials": author_score,
                "claims_accuracy": max(0, claims_score),
            },
            "rating": "Highly Credible" if overall_score >= 80 else "Credible" if overall_score >= 60 else "Questionable" if overall_score >= 40 else "Low Credibility",
            "recommendation": "Safe to share" if overall_score >= 70 else "Verify with additional sources" if overall_score >= 50 else "Not recommended as reliable health information",
        }

    def get_fact_check_response(self, claim: str) -> Dict:
        """Generate a fact-check response for a health claim"""
        verification = self.verify_claim(claim)

        response_parts = []
        if verification["verification"] == "misleading":
            response_parts.append(f"❌ This claim is misleading.")
            response_parts.append(f"Reality: {verification.get('reality', 'Not supported by evidence')}")
            response_parts.append(f"Trusted sources: {', '.join(verification.get('correct_sources', []))}")
        elif verification["verification"] == "unverified":
            response_parts.append(f"⚠️ This claim is unverified.")
            response_parts.append(f"Summary: {verification.get('summary', 'Insufficient evidence')}")
            response_parts.append(f"For accurate information, consult: {', '.join(verification.get('recommended_sources', []))}")

        return {
            "claim": claim,
            "response": " ".join(response_parts),
            "verification_status": verification["verification"],
            "confidence": verification["confidence"],
        }


health_misinformation_service = HealthMisinformationService()
