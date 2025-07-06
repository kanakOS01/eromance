from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db


app = FastAPI()

ORIGINS = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
async def heatlh(db: AsyncSession = Depends(get_db)):
    response = {'app': 'working', 'db': None}
    try:
        result = await db.execute(text("SELECT 'db working'"))
        response['db'] = result.scalar()
    except Exception as e:
        response['db'] = str(e)
    return response
