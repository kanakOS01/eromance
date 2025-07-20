from sqlalchemy import ARRAY, JSON, Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class Post(Base):
    __tablename__ = 'posts'

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    content = Column(JSON, nullable=False)
    tags = Column(ARRAY(String))
    views = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)
    deleted_at = Column(Integer, nullable=True)

    user = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")

    def __repr__(self):
        return f'<Post(id={self.id}, title={self.title}, slug={self.slug})>'