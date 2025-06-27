from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Hint(AsyncAttrs, Base):
    __tablename__ = "hints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code_name = Column(String, unique=True, nullable=False)
    hint_type = Column(String, nullable=False)  # 'text', 'image', 'video'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
