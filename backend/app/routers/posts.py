from datetime import datetime as dt
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.database import get_db
from app.schemas.post import PostCreate, PostOut
from app.models.post import Post
from app.utils import generate_unique_slug

router = APIRouter(prefix='/posts', tags=['Posts'])


@router.post('/')
async def create_post(
    post: PostCreate,
    db: AsyncConnection = Depends(get_db)
):
    """Create a new post."""
    try:
        slug_base = re.sub(r"[^\w]+", "-", post.title.lower()).strip("-")
        query = text("SELECT slug FROM post WHERE slug LIKE :like")
        result = await db.execute(query, {"like": f"{slug_base}%"})
        existing_slugs = {row.slug for row in result.mappings().all()}
        unique_slug = generate_unique_slug(post.title, existing_slugs)

        now = int(dt.now().timestamp())
        new_post = Post(
            **post.model_dump(),
            id = str(uuid.uuid4()),
            slug = unique_slug,
            created_at = now,
            updated_at = now,
            is_published = True,
        )
        db.add(new_post)
        await db.commit()
        await db.refresh(new_post)
        return { 'id': new_post.id }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while creating the post: {str(e)}"
        )
    

@router.get('/')
async def get_posts(db: AsyncConnection = Depends(get_db)) -> list[PostOut]:
    """Retrieve all posts."""
    try:
        query = text('SELECT id, slug, title, content, tags FROM post WHERE is_published = true ORDER BY created_at DESC')
        result = await db.execute(query)
        posts = result.mappings().all()
        return posts
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving posts: {str(e)}"
        )


@router.get('/{slug}')
async def get_post(slug: str, db: AsyncConnection = Depends(get_db)) -> PostOut:
    """Retrieve a single post by slug."""
    try:
        query = text('SELECT id, slug, title, content, tags FROM post WHERE slug = :slug AND is_published = true')
        result = await db.execute(query, {'slug': slug})
        post = result.mappings().first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving the post: {str(e)}"
        )