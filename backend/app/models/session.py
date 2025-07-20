from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.models.base import Base


class Session(Base):
    __tablename__ = 'sessions'

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    session_token = Column(String, unique=True, nullable=False)
    expires = Column(Integer, nullable=False)

    user = relationship('User', back_populates='sessions')

    def __repr__(self):
        return f'<Session(id={self.id}, user_id={self.user_id}, expires={self.expires})>'