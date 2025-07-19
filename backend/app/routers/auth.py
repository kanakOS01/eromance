import datetime
from datetime import datetime as dt, timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
import requests
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import text
from jose import JWTError, jwt


from app.settings import settings
from app.utils import create_access_token, log_token, log_user
from app.database import get_db


router = APIRouter(prefix='', tags=['auth'])


oauth = OAuth()
oauth.register(
    name='google_auth',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    refresh_token_url=None,
    authorize_state=settings.SECRET_KEY,
    redirect_uri='http://127.0.0.1:8000/auth',
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
    client_kwargs={'scope': 'openid profile email'},
)


@router.get('/login')
async def login(request: Request):
    request.session.clear()
    referer = request.headers.get('referer')
    frontend_url = settings.FRONTEND_URL
    redirect_url = settings.REDIRECT_URL
    request.session['login_redirect'] = frontend_url 

    return await oauth.google_auth.authorize_redirect(request, redirect_url, prompt='consent')


@router.get('/auth')
async def auth(request: Request, db: AsyncConnection = Depends(get_db)):
    try:
        token = await oauth.google_auth.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=401, detail='Google authentication failed.')

    try:
        user_info_endpoint = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f'Bearer {token['access_token']}'}
        google_response = requests.get(user_info_endpoint, headers=headers)
        user_info = google_response.json()
    except Exception as e:
        raise HTTPException(status_code=401, detail='Google authentication failed.')

    user = token.get('userinfo')
    google_id = user.get('sub')
    iss = user.get('iss')
    email = user.get('email')
    first_logged_in = dt.now(datetime.timezone.utc)
    last_accessed = dt.now(datetime.timezone.utc)

    name = user_info.get('name')
    image_url = user_info.get('picture')

    if iss not in ['https://accounts.google.com', 'accounts.google.com']:
        raise HTTPException(status_code=401, detail='Google authentication failed.')

    if google_id is None:
        raise HTTPException(status_code=401, detail='Google authentication failed.')

    access_token_expires = timedelta(days=7)
    access_token = await create_access_token(data={'sub': google_id, 'email': email}, expires_delta=access_token_expires)

    session_id = str(uuid.uuid4())
    await log_user(db, google_id, email, name, image_url, first_logged_in, last_accessed)
    await log_token(db, access_token, email, session_id, access_token_expires.total_seconds())

    redirect_url = request.session.pop('login_redirect', '')
    response = RedirectResponse(redirect_url)
    response.set_cookie(
        key='access_token',
        value=access_token,
        httponly=True,
        secure=True,
        samesite='strict',
    )

    return response


@router.get('/me')
async def get_me(request: Request):
    token = request.cookies.get('access_token')
    if not token:
        raise HTTPException(status_code=401, detail='Not authenticated')
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        google_id = payload.get('sub')
        email = payload.get('email')
        expires_at = dt.fromtimestamp(payload.get('exp', '0'))

        if expires_at < dt.now(datetime.timezone.utc):
            raise HTTPException(status_code=401, detail='Expired token')

        return {'google_id': google_id, 'email': email}
    except JWTError:
        raise HTTPException(status_code=401, detail='Invalid or expired token')
    

@router.get('/logout')
async def logout():
    response = RedirectResponse(url=settings.FRONTEND_URL)
    response.delete_cookie(key='access_token')
    return response
