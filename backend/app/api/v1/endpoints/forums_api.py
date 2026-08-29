"""Community Forums API — Posts, comments, likes, moderation"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.forums import forums_service

router = APIRouter()


class CreatePostRequest(BaseModel):
    user_id: str
    username: str
    category_id: str
    title: str
    content: str
    tags: list[str] = []


class CommentRequest(BaseModel):
    user_id: str
    username: str
    content: str


class ReportRequest(BaseModel):
    user_id: str
    reason: str


@router.get("/categories")
async def get_categories():
    return {"categories": forums_service.get_categories()}


@router.get("/posts")
async def get_posts(category_id: Optional[str] = None, trending: bool = False, search: str = "", limit: int = 20):
    return {"posts": forums_service.get_posts(category_id, trending, search, limit)}


@router.get("/posts/{post_id}")
async def get_post(post_id: str):
    post = forums_service.get_post(post_id)
    if not post:
        return {"error": "Post not found"}
    return {"post": post}


@router.post("/posts")
async def create_post(request: CreatePostRequest):
    return forums_service.create_post(request.user_id, request.username, request.category_id, request.title, request.content, request.tags)


@router.post("/posts/{post_id}/comment")
async def add_comment(post_id: str, request: CommentRequest):
    return forums_service.add_comment(post_id, request.user_id, request.username, request.content)


@router.post("/posts/{post_id}/like")
async def like_post(post_id: str, user_id: str = "anonymous"):
    return forums_service.like_post(post_id, user_id)


@router.post("/posts/{post_id}/report")
async def report_post(post_id: str, request: ReportRequest):
    return forums_service.report_post(post_id, request.user_id, request.reason)


@router.post("/posts/{post_id}/pin")
async def pin_post(post_id: str):
    return forums_service.pin_post(post_id)


@router.post("/posts/{post_id}/lock")
async def lock_post(post_id: str):
    return forums_service.lock_post(post_id)


@router.get("/trending")
async def get_trending(limit: int = 10):
    return {"trending": forums_service.get_trending(limit)}


@router.get("/reputation/{user_id}")
async def get_reputation(user_id: str):
    return forums_service.get_user_reputation(user_id)
