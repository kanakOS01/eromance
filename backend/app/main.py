from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import ORJSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers import posts, auth, comments
from app.settings import settings


app = FastAPI(root_path='/api', default_response_class=ORJSONResponse)
app.include_router(posts.router)
app.include_router(auth.router)
app.include_router(comments.router)


ORIGINS = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)


@app.get('/')
async def heatlh(db: AsyncSession = Depends(get_db)):
    response = {'app': 'working', 'db': None}
    try:
        result = await db.execute(text('SELECT "working"'))
        response['db'] = result.scalar()
    except Exception as e:
        response['db'] = str(e)
    return response
