from pydantic import BaseModel


class CommentCreateUpdate(BaseModel):
    content: str


class CommentOut(CommentCreateUpdate):
    comment_id: str
    post_id: str
    created_at: int
    user_name: str
    user_email: str
    user_image: str | None = None