"""
Community Forums — Posts, Comments, Likes, Reputation & Moderation

Features:
- Forum categories (nutrition, fitness, mental health, sleep, general)
- Post CRUD with rich content
- Comments and replies
- Likes and reactions
- User reputation system
- Moderation (report, pin, lock)
- Trending posts and search
"""
import time
import secrets
from typing import Optional
from dataclasses import dataclass, field


CATEGORIES = [
    {"id": "cat_001", "name": "General Health", "icon": "health", "color": "#6366F1", "post_count": 0, "description": "General health discussions and questions"},
    {"id": "cat_002", "name": "Fitness & Exercise", "icon": "fitness", "color": "#10B981", "post_count": 0, "description": "Workout tips, progress, and exercise advice"},
    {"id": "cat_003", "name": "Nutrition & Diet", "icon": "nutrition", "color": "#F97316", "post_count": 0, "description": "Recipes, meal plans, and nutrition advice"},
    {"id": "cat_004", "name": "Mental Health", "icon": "mental", "color": "#8B5CF6", "post_count": 0, "description": "Mental wellness, stress management, and support"},
    {"id": "cat_005", "name": "Sleep & Recovery", "icon": "sleep", "color": "#3B82F6", "post_count": 0, "description": "Sleep optimization and recovery strategies"},
    {"id": "cat_006", "name": "Weight Loss", "icon": "weight", "color": "#EF4444", "post_count": 0, "description": "Weight loss journeys, tips, and motivation"},
    {"id": "cat_007", "name": "Success Stories", "icon": "trophy", "color": "#EAB308", "post_count": 0, "description": "Share your health transformation stories"},
    {"id": "cat_008", "name": "Ask a Doctor", "icon": "doctor", "color": "#06B6D4", "post_count": 0, "description": "Medical questions answered by professionals"},
]


@dataclass
class Post:
    id: str
    user_id: str
    username: str
    category_id: str
    title: str
    content: str
    tags: list[str] = field(default_factory=list)
    likes: int = 0
    comment_count: int = 0
    is_pinned: bool = False
    is_locked: bool = False
    is_reported: bool = False
    created_at: float = field(default_factory=time.time)
    updated_at: float = 0


@dataclass
class Comment:
    id: str
    post_id: str
    user_id: str
    username: str
    content: str
    likes: int = 0
    created_at: float = field(default_factory=time.time)


class ForumsService:
    """Community forums with posts, comments, and moderation."""

    def __init__(self):
        self._categories = {c["id"]: c.copy() for c in CATEGORIES}
        self._posts: dict[str, Post] = {}
        self._comments: dict[str, list[Comment]] = {}
        self._likes: dict[str, set[str]] = {}  # post_id -> set of user_ids
        self._user_reputation: dict[str, int] = {}
        self._reports: list[dict] = []
        self._init_sample_posts()

    def _init_sample_posts(self):
        samples = [
            ("user_1", "FitFan", "cat_002", "My 30-day push-up challenge results!", "Started with 10 push-ups, now doing 50! Here's what worked for me...", ["fitness", "progress"]),
            ("user_2", "HealthNut", "cat_003", "Best meal prep strategies for busy professionals", "I've been meal prepping for 6 months and lost 20lbs. Here are my top 5 tips...", ["nutrition", "meal-prep"]),
            ("user_3", "ZenRunner", "cat_004", "How meditation changed my anxiety", "After years of struggling with anxiety, meditation has been a game-changer...", ["mental-health", "meditation"]),
            ("user_4", "SleepMaster", "cat_005", "Complete guide to sleep hygiene", "Here's everything I've learned about optimizing sleep quality...", ["sleep", "guide"]),
            ("user_5", "TransformMe", "cat_007", "Lost 50lbs in 6 months - my story", "From 250lbs to 200lbs. It wasn't easy but here's how I did it...", ["weight-loss", "success"]),
        ]
        for uid, uname, cat_id, title, content, tags in samples:
            post_id = f"post_{secrets.token_hex(6)}"
            self._posts[post_id] = Post(id=post_id, user_id=uid, username=uname, category_id=cat_id, title=title, content=content, tags=tags, likes=5, comment_count=3)
            self._categories[cat_id]["post_count"] = self._categories[cat_id].get("post_count", 0) + 1
            self._likes[post_id] = {uid}

    def get_categories(self) -> list[dict]:
        return list(self._categories.values())

    def get_posts(self, category_id: Optional[str] = None, trending: bool = False, search: str = "", limit: int = 20) -> list[dict]:
        posts = list(self._posts.values())
        if category_id:
            posts = [p for p in posts if p.category_id == category_id]
        if search:
            q = search.lower()
            posts = [p for p in posts if q in p.title.lower() or q in p.content.lower() or any(q in t for t in p.tags)]
        if trending:
            posts = sorted(posts, key=lambda p: p.likes + p.comment_count * 2, reverse=True)
        else:
            pinned = [p for p in posts if p.is_pinned]
            rest = sorted([p for p in posts if not p.is_pinned], key=lambda p: p.created_at, reverse=True)
            posts = pinned + rest
        return [{"id": p.id, "user_id": p.user_id, "username": p.username, "category_id": p.category_id, "title": p.title, "content": p.content, "tags": p.tags, "likes": p.likes, "comment_count": p.comment_count, "is_pinned": p.is_pinned, "created_at": p.created_at} for p in posts[:limit]]

    def get_post(self, post_id: str) -> Optional[dict]:
        p = self._posts.get(post_id)
        if not p:
            return None
        comments = self._comments.get(post_id, [])
        return {"id": p.id, "user_id": p.user_id, "username": p.username, "category_id": p.category_id, "title": p.title, "content": p.content, "tags": p.tags, "likes": p.likes, "comment_count": p.comment_count, "is_pinned": p.is_pinned, "is_locked": p.is_locked, "created_at": p.created_at, "comments": [{"id": c.id, "user_id": c.user_id, "username": c.username, "content": c.content, "likes": c.likes, "created_at": c.created_at} for c in comments]}

    def create_post(self, user_id: str, username: str, category_id: str, title: str, content: str, tags: list[str] = None) -> dict:
        if category_id not in self._categories:
            return {"error": "Category not found"}
        post_id = f"post_{secrets.token_hex(6)}"
        post = Post(id=post_id, user_id=user_id, username=username, category_id=category_id, title=title, content=content, tags=tags or [])
        self._posts[post_id] = post
        self._categories[category_id]["post_count"] = self._categories[category_id].get("post_count", 0) + 1
        self._user_reputation[user_id] = self._user_reputation.get(user_id, 0) + 10
        return {"post": {"id": post_id, "title": title, "category": category_id}}

    def add_comment(self, post_id: str, user_id: str, username: str, content: str) -> dict:
        post = self._posts.get(post_id)
        if not post:
            return {"error": "Post not found"}
        if post.is_locked:
            return {"error": "Post is locked"}
        comment_id = f"comment_{secrets.token_hex(6)}"
        comment = Comment(id=comment_id, post_id=post_id, user_id=user_id, username=username, content=content)
        self._comments.setdefault(post_id, []).append(comment)
        post.comment_count += 1
        self._user_reputation[user_id] = self._user_reputation.get(user_id, 0) + 5
        return {"comment": {"id": comment_id, "content": content}}

    def like_post(self, post_id: str, user_id: str) -> dict:
        post = self._posts.get(post_id)
        if not post:
            return {"error": "Post not found"}
        liked_users = self._likes.setdefault(post_id, set())
        if user_id in liked_users:
            liked_users.discard(user_id)
            post.likes = max(0, post.likes - 1)
            return {"liked": False, "likes": post.likes}
        liked_users.add(user_id)
        post.likes += 1
        return {"liked": True, "likes": post.likes}

    def report_post(self, post_id: str, user_id: str, reason: str) -> dict:
        post = self._posts.get(post_id)
        if not post:
            return {"error": "Post not found"}
        post.is_reported = True
        self._reports.append({"post_id": post_id, "user_id": user_id, "reason": reason, "created_at": time.time()})
        return {"reported": True}

    def pin_post(self, post_id: str) -> dict:
        post = self._posts.get(post_id)
        if not post:
            return {"error": "Post not found"}
        post.is_pinned = not post.is_pinned
        return {"pinned": post.is_pinned}

    def lock_post(self, post_id: str) -> dict:
        post = self._posts.get(post_id)
        if not post:
            return {"error": "Post not found"}
        post.is_locked = not post.is_locked
        return {"locked": post.is_locked}

    def get_trending(self, limit: int = 10) -> list[dict]:
        posts = sorted(self._posts.values(), key=lambda p: p.likes + p.comment_count * 2, reverse=True)
        return [{"id": p.id, "title": p.title, "username": p.username, "likes": p.likes, "comment_count": p.comment_count, "category_id": p.category_id} for p in posts[:limit]]

    def get_user_reputation(self, user_id: str) -> dict:
        return {"user_id": user_id, "reputation": self._user_reputation.get(user_id, 0), "level": self._get_level(self._user_reputation.get(user_id, 0))}

    def _get_level(self, rep: int) -> str:
        if rep >= 1000: return "Legend"
        if rep >= 500: return "Expert"
        if rep >= 200: return "Contributor"
        if rep >= 50: return "Member"
        return "Newcomer"

    def get_reports(self, limit: int = 50) -> list[dict]:
        return self._reports[:limit]


forums_service = ForumsService()
