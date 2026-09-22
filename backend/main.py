"""
main.py — FastAPI application for the Content Intelligence Platform.
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from . import crud, schemas, models
from .database import engine, get_db
from .ai import run_ai_analysis, transform_content

# Create all tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Content Intelligence Platform API",
    description="AI-powered content analysis and transformation backend.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Users ───────────────────────────────────────────────────────────────────

@app.post("/users", response_model=schemas.UserOut, tags=["Users"])
def create_or_get_user(data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Get existing user by name, or create a new one."""
    return crud.get_or_create_user(db, data.name.strip())


@app.get("/users", response_model=List[schemas.UserOut], tags=["Users"])
def list_users(db: Session = Depends(get_db)):
    return crud.list_users(db)


# ─── Content ─────────────────────────────────────────────────────────────────

@app.post("/content", response_model=schemas.ContentOut, tags=["Content"])
def save_content(data: schemas.ContentCreate, db: Session = Depends(get_db)):
    """Save a new piece of content for a user."""
    # Validate user exists
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_content(db, data)


@app.get("/content/user/{user_id}", response_model=List[schemas.ContentListItem], tags=["Content"])
def list_content(user_id: int, db: Session = Depends(get_db)):
    """List all content for a specific user (newest first)."""
    return crud.list_content_by_user(db, user_id)


@app.get("/content/item/{content_id}", response_model=schemas.ContentOut, tags=["Content"])
def get_content(content_id: int, db: Session = Depends(get_db)):
    """Get a single content item with all outputs and tags."""
    content = crud.get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content


@app.delete("/content/{content_id}", tags=["Content"])
def delete_content(content_id: int, db: Session = Depends(get_db)):
    """Delete a content item and all associated outputs/tags."""
    if not crud.delete_content(db, content_id):
        raise HTTPException(status_code=404, detail="Content not found")
    return {"detail": "Deleted"}


# ─── AI Processing ───────────────────────────────────────────────────────────

@app.post("/ai/analyze/{content_id}", tags=["AI"])
def analyze_content(content_id: int, db: Session = Depends(get_db)):
    """
    Run AI analysis on a content item.
    Returns the raw AI results WITHOUT saving — caller decides what to save.
    """
    content = crud.get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    try:
        results = run_ai_analysis(content.original_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")
    return results


@app.post("/ai/transform/{content_id}", tags=["AI"])
def transform_content_route(
    content_id: int,
    request: schemas.TransformRequest,
    db: Session = Depends(get_db),
):
    """
    Transform content into a target format.
    Returns the raw transformed text WITHOUT saving — caller decides what to save.
    """
    content = crud.get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    try:
        result = transform_content(content.original_text, request.format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transform failed: {str(e)}")
    return {"format": request.format, "text": result}


# ─── Save / Edit Generated Outputs ──────────────────────────────────────────

@app.post("/outputs/{content_id}", response_model=List[schemas.GeneratedOutputOut], tags=["Outputs"])
def save_outputs(
    content_id: int,
    request: schemas.SaveOutputsRequest,
    db: Session = Depends(get_db),
):
    """Batch-save (upsert) multiple generated outputs for a content item."""
    content = crud.get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    saved = []
    for item in request.outputs:
        output = crud.save_output(db, content_id, item["output_type"], item["text"])
        saved.append(output)
    return saved


@app.put("/outputs/{output_id}", response_model=schemas.GeneratedOutputOut, tags=["Outputs"])
def edit_output(
    output_id: int,
    data: schemas.OutputUpdate,
    db: Session = Depends(get_db),
):
    """Edit a single generated output by its ID."""
    output = crud.update_output(db, output_id, data.text)
    if not output:
        raise HTTPException(status_code=404, detail="Output not found")
    return output


# ─── Tags ────────────────────────────────────────────────────────────────────

@app.post("/tags/{content_id}", response_model=schemas.TagOut, tags=["Tags"])
def add_tag(content_id: int, data: schemas.TagCreate, db: Session = Depends(get_db)):
    """Add a tag to a content item."""
    content = crud.get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return crud.add_tag(db, content_id, data.label)


@app.delete("/tags/{tag_id}", tags=["Tags"])
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    """Delete a tag by ID."""
    if not crud.delete_tag(db, tag_id):
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"detail": "Tag deleted"}


# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

@app.post(/"ai/transform-all/{content_id}/", tags=["AI"])
def transform_all_content_route(content_id: int, db: Session = Depends(get_db)):
    from .ai import run_ai_transform_all
    content = crud.get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    try:
        results = run_ai_transform_all(content.original_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI transform-all failed: {str(e)}")
    return results
