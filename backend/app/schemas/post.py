from pydantic import BaseModel


class PostCreate(BaseModel):
    title: str
    content: str
    tags: list[str] | None = None


class PostOut(PostCreate):
    id: str
    slug: str