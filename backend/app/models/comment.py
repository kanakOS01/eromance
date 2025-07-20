from sqlalchemy import ARRAY, JSON, Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    post_id = Column(String, ForeignKey("posts.id"), nullable=False)
    content = Column(JSON, nullable=False)
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(Integer, nullable=True)

    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")

    def __repr__(self):
        return f'<Comment(id={self.id}, user_id={self.user_id}, post_id={self.post_id})>'