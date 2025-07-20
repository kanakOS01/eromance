from datetime import datetime as dt
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.database import get_db
from app.schemas.post import PostCreateUpdate, PostOut
from app.models.post import Post
from app.utils import generate_unique_slug, get_current_user

router = APIRouter(prefix='/posts', tags=['Posts'])


@router.post('/')
async def create_post(
    post: PostCreateUpdate,
    db: AsyncConnection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    '''Create a new post.'''
    try:
        user_id = user.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail='Unauthorized')
        
        slug_base = re.sub(r'[^\w]+', '-', post.title.lower()).strip('-')
        query = text('SELECT slug FROM posts WHERE slug LIKE :like')
        result = await db.execute(query, {'like': f'{slug_base}%'})
        existing_slugs = {row.slug for row in result.mappings().all()}
        unique_slug = await generate_unique_slug(post.title, existing_slugs)

        now = int(dt.now().timestamp())
        new_post = Post(
            **post.model_dump(),
            id = str(uuid.uuid4()),
            slug = unique_slug,
            created_at = now,
            updated_at = now,
            is_published = True,
            user_id = user_id,
        )
        db.add(new_post)
        await db.commit()
        await db.refresh(new_post)
        return { 'id': new_post.id }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f'An error occurred while creating the post: {str(e)}'
        )
    

@router.get('/')
async def get_posts(db: AsyncConnection = Depends(get_db)) -> list[PostOut]:
    '''Retrieve all posts.'''
    try:
        query = text('''
            SELECT 
                posts.id, posts.slug, posts.title, posts.content, posts.tags,
                users.name AS user_name, users.email AS user_email, users.image AS user_image
            FROM posts
            JOIN users ON posts.user_id = users.id
            WHERE posts.is_published = true
            ORDER BY posts.created_at DESC
        ''')
        result = await db.execute(query)
        posts = result.mappings().all()
        return posts
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'An error occurred while retrieving posts: {str(e)}'
        )


@router.get('/{slug}')
async def get_post(slug: str, db: AsyncConnection = Depends(get_db)) -> PostOut:
    '''Retrieve a single post by slug.'''
    try:
        query = text('''
            SELECT 
                posts.id, posts.slug, posts.title, posts.content, posts.tags,
                users.id AS user_id, users.name AS user_name, users.email AS user_email, users.image AS user_image
            FROM posts
            JOIN users ON posts.user_id = users.id
            WHERE posts.slug = :slug AND posts.is_published = true
            LIMIT 1
        ''')
        result = await db.execute(query, {'slug': slug})
        post = result.mappings().first()
        if not post:
            raise HTTPException(status_code=404, detail='Post not found')
        return post
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'An error occurred while retrieving the post: {str(e)}'
        )


@router.delete('/{slug}')
async def delete_post(
    slug: str,
    db: AsyncConnection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    '''Delete a post by slug.'''
    try:
        user_id = user.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail='Unauthorized')

        query = text('''
            DELETE FROM posts 
            WHERE slug = :slug AND user_id = :user_id
        ''')
        result = await db.execute(query, {'slug': slug, 'user_id': user_id})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail='Post not found or unauthorized')

        await db.commit()
        return {'detail': 'Post deleted successfully'}
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f'An error occurred while deleting the post: {str(e)}'
        )


@router.put('/{slug}')
async def update_post(
    slug: str,
    post: PostCreateUpdate,
    db: AsyncConnection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    '''Update an existing post by slug.'''
    try:
        user_id = user.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail='Unauthorized')

        query = text('''
            SELECT id FROM posts 
            WHERE slug = :slug AND user_id = :user_id
            LIMIT 1
        ''')
        result = await db.execute(query, {'slug': slug, 'user_id': user_id})
        post_id = result.scalar_one_or_none()

        if not post_id:
            raise HTTPException(status_code=404, detail='Post not found or unauthorized')

        existing_post = await db.get(Post, post_id)
        if not existing_post:
            raise HTTPException(status_code=404, detail='Post record could not be loaded')

        for key, value in post.model_dump().items():
            setattr(existing_post, key, value)

        existing_post.updated_at = int(dt.now().timestamp())

        await db.commit()
        await db.refresh(existing_post)
        return {'id': existing_post.id}

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f'An error occurred while updating the post: {str(e)}'
        )
