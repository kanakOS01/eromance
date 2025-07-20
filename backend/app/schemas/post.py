from pydantic import BaseModel


class PostCreateUpdate(BaseModel):
    title: str
    content: str
    tags: list[str] | None = None


class PostOut(PostCreateUpdate):
    id: str
    slug: str
    user_name: str
    user_email: str
    user_image: str | None = None