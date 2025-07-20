from datetime import (
    datetime as dt,
    timedelta
)
import datetime
import re
import uuid
import traceback

from jose import jwt, ExpiredSignatureError, JWTError
from fastapi import HTTPException, Cookie
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import text
from fastapi import Depends

from app.settings import settings
from app.database import get_db


async def generate_unique_slug(title: str, existing_slugs: set[str]) -> str:
    base_slug = re.sub(r'[^\w]+', '-', title.lower()).strip('-')
    slug = base_slug
    suffix = 1
    while slug in existing_slugs:
        slug = f'{base_slug}_{suffix}'
        suffix += 1
    return slug


async def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = dt.now(datetime.timezone.utc) + (expires_delta or timedelta(minutes=600))
    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def log_user(
    db: AsyncConnection,
    google_id: str,
    email: str,
    name: str,
    image_url: str,
    first_logged_in: dt,
    last_accessed: dt,
):
    try:
        check_query = text('SELECT 1 FROM users WHERE email = :email')
        result = await db.execute(check_query, {'email': email})
        user = result.fetchone()

        if user:
            update_query = text('''
                UPDATE users
                SET email = :email,
                    name = :name,
                    image = :image,
                    updated_at = :updated_at
                WHERE google_id = :google_id
            ''')
            await db.execute(update_query, {
                'email': email,
                'name': name,
                'image': image_url,
                'updated_at': int(last_accessed.timestamp()),
                'google_id': google_id,
            })
        else:
            insert_query = text('''
                INSERT INTO users (id, google_id, email, name, image, created_at, updated_at)
                VALUES (:id, :google_id, :email, :name, :image, :created_at, :updated_at)
            ''')
            await db.execute(insert_query, {
                'id': str(uuid.uuid4()),
                'google_id': google_id,
                'email': email,
                'name': name,
                'image': image_url,
                'created_at': int(first_logged_in.timestamp()),
                'updated_at': int(last_accessed.timestamp()),
            })

        await db.commit()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail='Internal server error logging user')


async def log_token(
    db: AsyncConnection,
    access_token: str,
    email: str,
    session_id: str,
    expires_in: int = 86400,
):
    try:
        user_query = text('SELECT id FROM users WHERE email = :email')
        user_result = await db.execute(user_query, {'email': email})
        user = user_result.fetchone()
        if not user:
            return

        insert_query = text('''
            INSERT INTO sessions (id, user_id, session_token, expires)
            VALUES (:id, :user_id, :token, :expires)
        ''')
        await db.execute(insert_query, {
            'id': session_id,
            'user_id': user.id,
            'token': access_token,
            'expires': int((dt.now(datetime.timezone.utc) + timedelta(seconds=expires_in)).timestamp()),
        })

        await db.commit()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail='Internal server error logging token')
    

async def get_current_user(token: str = Cookie(None, alias='access_token'), db: AsyncConnection = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail='Not authenticated')

    credentials_exception = HTTPException(
        status_code=401,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        google_id: str = payload.get('sub')
        email: str = payload.get('email')
        if google_id is None or email is None:
            raise credentials_exception
        
        query = text('SELECT id FROM users WHERE google_id = :google_id AND email = :email LIMIT 1')
        result = await db.execute(query, {"google_id": google_id, 'email': email})
        user_data = result.mappings().first()

        if not user_data:
            raise HTTPException(status_code=404, detail='User not found')

        return {'google_id': google_id, 'email': email, 'user_id': user_data.id}

    except ExpiredSignatureError:
        traceback.print_exc()
        raise HTTPException(status_code=401, detail='Session expired. Please login again.')
    except JWTError:
        traceback.print_exc()
        raise credentials_exception
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=401, detail='Not Authenticated')
