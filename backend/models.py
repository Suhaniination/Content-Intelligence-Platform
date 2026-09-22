"""
models.py — SQLAlchemy ORM models for the Content Intelligence Platform.

Entities:
  User            — id, name
  Content         — id, user_id, title, original_text, created_at
  GeneratedOutput — id, content_id, output_type, text, created_at
  Tag             — id, content_id, label
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)

    contents = relationship("Content", back_populates="user", cascade="all, delete-orphan")


class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(300), nullable=False, default="Untitled")
    original_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="contents")
    outputs = relationship("GeneratedOutput", back_populates="content", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="content", cascade="all, delete-orphan")


class GeneratedOutput(Base):
    """
    output_type values:
      summary | key_points | keywords | topics | tags |
      faq | social_post | email_summary | press_release
    """
    __tablename__ = "generated_outputs"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False)
    output_type = Column(String(50), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    content = relationship("Content", back_populates="outputs")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False)
    label = Column(String(100), nullable=False)

    content = relationship("Content", back_populates="tags")
