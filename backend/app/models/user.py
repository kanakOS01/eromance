from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True)
    google_id = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    image = Column(String, nullable=True)
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)

    sessions = relationship("Session", back_populates="user")

    def __repr__(self):
        return f'<User(id={self.id}, email={self.email}, name={self.name})>'
