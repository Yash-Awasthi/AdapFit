"""
YouTube search backed by yt-dlp.

Returns the video id, title, channel, duration, and thumbnail needed to render
a content card and an embed, without a Google API key or quota. Extraction is
flat, so a search costs one request and never touches a video's formats.
"""
import asyncio
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    from yt_dlp import YoutubeDL
except ImportError:  # pragma: no cover - server still boots without the extra
    YoutubeDL = None

EMBED_TEMPLATE = "https://www.youtube-nocookie.com/embed/{video_id}?rel=0&playsinline=1"
WATCH_TEMPLATE = "https://www.youtube.com/watch?v={video_id}"
THUMBNAIL_TEMPLATE = "https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

_YDL_OPTIONS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "extract_flat": "in_playlist",
    "noplaylist": False,
    "socket_timeout": 12,
}

CACHE_TTL_SECONDS = 60 * 60 * 6
_cache: dict[str, tuple[float, list[dict]]] = {}


def search_available() -> bool:
    return YoutubeDL is not None


def _normalise(entry: dict[str, Any]) -> Optional[dict]:
    video_id = entry.get("id")
    if not video_id or len(video_id) != 11:
        return None

    duration = entry.get("duration")
    return {
        "video_id": video_id,
        "title": entry.get("title") or "Untitled",
        "channel": entry.get("uploader") or entry.get("channel") or "",
        "duration_seconds": int(duration) if isinstance(duration, (int, float)) else 0,
        "view_count": entry.get("view_count") or 0,
        "thumbnail_url": THUMBNAIL_TEMPLATE.format(video_id=video_id),
        "watch_url": WATCH_TEMPLATE.format(video_id=video_id),
        "embed_url": EMBED_TEMPLATE.format(video_id=video_id),
    }


def _search_blocking(query: str, limit: int) -> list[dict]:
    with YoutubeDL(_YDL_OPTIONS) as ydl:
        result = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)

    entries = result.get("entries") or [] if isinstance(result, dict) else []
    return [item for item in (_normalise(e) for e in entries if isinstance(e, dict)) if item]


async def search(query: str, limit: int = 12) -> list[dict]:
    """
    Search YouTube, returning at most `limit` renderable results.

    Results are cached because an extraction takes seconds and the same
    category queries repeat on every feed load. An empty list means the
    search failed or yt-dlp is not installed; callers fall back to a link.
    """
    query = query.strip()
    if not query or YoutubeDL is None:
        return []

    key = f"{query}::{limit}"
    cached = _cache.get(key)
    if cached and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    try:
        # yt-dlp is synchronous and network-bound, so it must not run on the
        # event loop or it blocks every other request for its duration.
        items = await asyncio.to_thread(_search_blocking, query, limit)
    except Exception as exc:
        logger.warning("YouTube search failed for %r: %s", query, exc)
        return []

    _cache[key] = (time.monotonic(), items)
    return items
