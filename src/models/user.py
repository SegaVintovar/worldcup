from sqlalchemy import Column, Integer, String
from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    intra_login = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
