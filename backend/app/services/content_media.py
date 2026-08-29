"""
Media resolution for the content hub.

The seeded library ships titles and descriptions but no playable media. This
module maps a content title onto a real video, and gives every other item a
YouTube search link so a card is never a dead end.

Extending: add an entry to YOUTUBE_IDS keyed by a lowercase substring of the
content title. Anything without an entry falls back to search.
"""
from typing import Optional
from urllib.parse import quote_plus

# Verified video ids, keyed by a lowercase substring of the content title.
YOUTUBE_IDS: dict[str, str] = {
    "barbell back squat": "bEv6CCg2BC8",
    "front squat": "v-mQm_droHg",
    "deadlift": "DQGHPLs9N6Y",
    "bench press": "DQGHPLs9N6Y",
    "overhead press": "DQGHPLs9N6Y",
    "barbell row": "DQGHPLs9N6Y",
}

THUMBNAIL_TEMPLATE = "https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
WATCH_TEMPLATE = "https://www.youtube.com/watch?v={video_id}"
EMBED_TEMPLATE = "https://www.youtube-nocookie.com/embed/{video_id}?rel=0&playsinline=1"
SEARCH_TEMPLATE = "https://www.youtube.com/results?search_query={query}"


def youtube_id_for(title: str) -> Optional[str]:
    """Curated video id for a content title, or None when nothing matches."""
    lowered = title.lower()
    for keyword, video_id in YOUTUBE_IDS.items():
        if keyword in lowered:
            return video_id
    return None


def media_for(title: str, category: str = "") -> dict:
    """
    Playable media for a content item.

    Always returns a usable `search_url`; `video_id`, `thumbnail_url` and
    `embed_url` are only present for titles with a curated video.
    """
    query = quote_plus(f"{title} {category} tutorial".strip())
    video_id = youtube_id_for(title)
    media = {
        "video_id": video_id,
        "thumbnail_url": THUMBNAIL_TEMPLATE.format(video_id=video_id) if video_id else None,
        "watch_url": WATCH_TEMPLATE.format(video_id=video_id) if video_id else None,
        "embed_url": EMBED_TEMPLATE.format(video_id=video_id) if video_id else None,
        "search_url": SEARCH_TEMPLATE.format(query=query),
    }
    return media
