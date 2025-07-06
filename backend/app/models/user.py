from sqlalchemy import Boolean, Column, Integer, String
from app.models.base import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)

    def __repr__(self):
        return f'<User(id={self.id}, email={self.email}, username={self.username})>'
