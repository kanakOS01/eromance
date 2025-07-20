from datetime import datetime as dt
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.database import get_db
from app.models.comment import Comment
from app.utils import get_current_user
from app.schemas.comment import CommentCreateUpdate, CommentOut


router = APIRouter(prefix='/comments', tags=['Comments'])


@router.post('/')
async def create_comment(
    post_id: str,
    comment: CommentCreateUpdate,
    db: AsyncConnection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    '''Create a new comment.'''
    try:
        user_id = user.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail='Unauthorized')

        now = int(dt.now().timestamp())
        new_comment = Comment(
            id=str(uuid.uuid4()),
            post_id=post_id,
            content=comment.content,
            user_id=user_id,
            created_at=now,
            updated_at=now,
        )
        db.add(new_comment)
        await db.commit()
        await db.refresh(new_comment)
        return new_comment
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f'An error occurred while creating the comment: {str(e)}'
        )
    

@router.get('/{post_id}')
async def get_comments(
    post_id: str,
    db: AsyncConnection = Depends(get_db)
) -> list[CommentOut]:
    '''Get comments with user info for a specific post.'''
    try:
        query = text("""
            SELECT 
                c.id AS comment_id,
                c.post_id,
                c.content,
                c.created_at,
                u.name AS user_name,
                u.email AS user_email,
                u.image AS user_image
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = :post_id AND c.is_deleted = false
            ORDER BY c.created_at ASC
        """)
        result = await db.execute(query, {'post_id': post_id})
        comments = result.mappings().all()
        return comments
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'An error occurred while fetching comments: {str(e)}'
        )


@router.delete('/{comment_id}')
async def delete_comment(
    comment_id: str,
    db: AsyncConnection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    '''Delete a comment by ID.'''
    try:
        user_id = user.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail='Unauthorized')

        comment = await db.get(Comment, comment_id)
        if not comment or comment.user_id != user_id:
            raise HTTPException(status_code=404, detail='Comment not found or unauthorized')

        comment.is_deleted = True
        comment.deleted_at = int(dt.now().timestamp())
        await db.commit()
        return {'detail': 'Comment deleted successfully'}
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f'An error occurred while deleting the comment: {str(e)}'
        )
    

@router.put('/{comment_id}')
async def update_comment(
    comment_id: str,
    updated_comment: CommentCreateUpdate,
    db: AsyncConnection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    '''Update a comment by ID.'''
    try:
        user_id = user.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail='Unauthorized')

        comment = await db.get(Comment, comment_id)
        if not comment or comment.user_id != user_id:
            raise HTTPException(status_code=404, detail='Comment not found or unauthorized')
        if comment.is_deleted:
            raise HTTPException(status_code=404, detail='Comment is deleted')

        comment.content = updated_comment.content
        comment.updated_at = int(dt.now().timestamp())
        await db.commit()
        return {'detail': 'Comment updated successfully'}
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f'An error occurred while updating the comment: {str(e)}'
        )
