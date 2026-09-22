"""
crud.py — Database CRUD operations for the Content Intelligence Platform.
"""

from sqlalchemy.orm import Session
from . import models, schemas


# ─── User ────────────────────────────────────────────────────────────────────

def get_or_create_user(db: Session, name: str) -> models.User:
    user = db.query(models.User).filter(models.User.name == name).first()
    if not user:
        user = models.User(name=name)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def list_users(db: Session):
    return db.query(models.User).order_by(models.User.name).all()


# ─── Content ─────────────────────────────────────────────────────────────────

def create_content(db: Session, data: schemas.ContentCreate) -> models.Content:
    content = models.Content(
        user_id=data.user_id,
        title=data.title or "Untitled",
        original_text=data.original_text,
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    return content


def get_content(db: Session, content_id: int) -> models.Content | None:
    return db.query(models.Content).filter(models.Content.id == content_id).first()


def list_content_by_user(db: Session, user_id: int):
    return (
        db.query(models.Content)
        .filter(models.Content.user_id == user_id)
        .order_by(models.Content.created_at.desc())
        .all()
    )


def delete_content(db: Session, content_id: int) -> bool:
    content = get_content(db, content_id)
    if not content:
        return False
    db.delete(content)
    db.commit()
    return True


# ─── GeneratedOutput ─────────────────────────────────────────────────────────

def save_output(db: Session, content_id: int, output_type: str, text: str) -> models.GeneratedOutput:
    """Insert or replace a generated output of a given type for a content item."""
    existing = (
        db.query(models.GeneratedOutput)
        .filter(
            models.GeneratedOutput.content_id == content_id,
            models.GeneratedOutput.output_type == output_type,
        )
        .first()
    )
    if existing:
        existing.text = text
        db.commit()
        db.refresh(existing)
        return existing

    output = models.GeneratedOutput(content_id=content_id, output_type=output_type, text=text)
    db.add(output)
    db.commit()
    db.refresh(output)
    return output


def get_outputs_by_content(db: Session, content_id: int):
    return (
        db.query(models.GeneratedOutput)
        .filter(models.GeneratedOutput.content_id == content_id)
        .order_by(models.GeneratedOutput.created_at)
        .all()
    )


def update_output(db: Session, output_id: int, text: str) -> models.GeneratedOutput | None:
    output = db.query(models.GeneratedOutput).filter(models.GeneratedOutput.id == output_id).first()
    if not output:
        return None
    output.text = text
    db.commit()
    db.refresh(output)
    return output


# ─── Tags ────────────────────────────────────────────────────────────────────

def add_tag(db: Session, content_id: int, label: str) -> models.Tag:
    tag = models.Tag(content_id=content_id, label=label.strip())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def delete_tag(db: Session, tag_id: int) -> bool:
    tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if not tag:
        return False
    db.delete(tag)
    db.commit()
    return True


def list_tags(db: Session, content_id: int):
    return db.query(models.Tag).filter(models.Tag.content_id == content_id).all()
