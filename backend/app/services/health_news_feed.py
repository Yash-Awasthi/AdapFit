"""
Health News & Evidence Feed — Core content from authoritative sources.
"""
import time
from typing import Optional
from dataclasses import dataclass, field


class ContentCategory:
    HEALTH = "health"
    FITNESS = "fitness"
    SLEEP = "sleep"
    MENTAL = "mental_wellbeing"
    RESEARCH = "research"
    NUTRITION = "nutrition"


class EvidenceLevel:
    PEER_REVIEWED = "peer_reviewed"
    GOVERNMENT = "government_agency"
    MEDICAL_ORG = "medical_organization"


@dataclass
class HealthArticle:
    id: str
    title: str
    summary: str
    why_it_matters: str
    category: str
    content_type: str
    evidence_level: str
    source_name: str
    source_url: str
    publish_date: str
    tags: list = field(default_factory=list)
    relevance_tags: list = field(default_factory=list)


class HealthNewsFeedService:
    def __init__(self):
        self._articles: dict[str, HealthArticle] = {}
        self._load_content()

    def _load_content(self):
        articles = [
            HealthArticle(
                id="who_sleep", title="WHO Sleep Recommendations for Adults",
                summary="Adults should aim for 7-9 hours of sleep per night with consistent schedules.",
                why_it_matters="Sleep deprivation increases risk of cardiovascular disease, obesity, and impaired immunity.",
                category="sleep", content_type="medical_guidance", evidence_level=EvidenceLevel.GOVERNMENT,
                source_name="WHO", source_url="https://www.who.int/news-room/fact-sheets/detail/sleep",
                publish_date="2024-01-01", tags=["sleep", "guidelines"],
                relevance_tags=["poor_sleep", "sleep_debt"],
            ),
            HealthArticle(
                id="nih_exercise", title="Physical Activity Guidelines",
                summary="150 min/week moderate aerobic activity + muscle-strengthening 2+ days.",
                why_it_matters="Reduces heart disease, diabetes, cancer, and depression risk.",
                category="fitness", content_type="medical_guidance", evidence_level=EvidenceLevel.GOVERNMENT,
                source_name="HHS", source_url="https://health.gov/physicalactivity/current-guidelines",
                publish_date="2024-01-01", tags=["exercise", "guidelines"],
                relevance_tags=["low_activity", "sedentary"],
            ),
            HealthArticle(
                id="stress_mgmt", title="Evidence-Based Stress Management",
                summary="Deep breathing, progressive muscle relaxation, and meditation reduce stress.",
                why_it_matters="Chronic stress contributes to heart disease, depression, and weakened immunity.",
                category="mental_wellbeing", content_type="education", evidence_level=EvidenceLevel.MEDICAL_ORG,
                source_name="APA", source_url="https://www.apa.org/topics/stress",
                publish_date="2024-06-01", tags=["stress", "meditation"],
                relevance_tags=["high_stress", "high_anxiety"],
            ),
            HealthArticle(
                id="screen_sleep", title="Screen Time Before Bed Disrupts Sleep",
                summary="Blue light suppresses melatonin. Avoid screens 1-2 hours before bed.",
                why_it_matters="Late-night screen use is a top cause of poor sleep quality in the digital age.",
                category="research", content_type="research", evidence_level=EvidenceLevel.PEER_REVIEWED,
                source_name="Journal of Sleep Research", source_url="https://onlinelibrary.wiley.com/journal/13652869",
                publish_date="2025-03-15", tags=["screen_time", "sleep"],
                relevance_tags=["poor_sleep", "high_screen_time"],
            ),
        ]
        for a in articles:
            self._articles[a.id] = a

    def get_feed(self, category: Optional[str] = None, content_type: Optional[str] = None,
                 evidence_level: Optional[str] = None, limit: int = 20) -> list[dict]:
        articles = list(self._articles.values())
        if category:
            articles = [a for a in articles if a.category == category]
        if content_type:
            articles = [a for a in articles if a.content_type == content_type]
        if evidence_level:
            articles = [a for a in articles if a.evidence_level == evidence_level]
        articles.sort(key=lambda a: a.publish_date, reverse=True)
        return [self._to_dict(a) for a in articles[:limit]]

    def get_article(self, article_id: str) -> Optional[dict]:
        a = self._articles.get(article_id)
        return self._to_dict(a) if a else None

    def get_categories(self) -> list[dict]:
        cats = {}
        for a in self._articles.values():
            cats[a.category] = cats.get(a.category, 0) + 1
        return [{"id": k, "name": k.replace("_", " ").title(), "count": v} for k, v in cats.items()]

    def _to_dict(self, a: HealthArticle) -> dict:
        return {
            "id": a.id, "title": a.title, "summary": a.summary,
            "why_it_matters": a.why_it_matters, "category": a.category,
            "content_type": a.content_type, "evidence_level": a.evidence_level,
            "source_name": a.source_name, "source_url": a.source_url,
            "publish_date": a.publish_date, "tags": a.tags,
        }


health_news_feed_service = HealthNewsFeedService()
