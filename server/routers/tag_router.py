from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.models import Tag
from schemas.tag_schema import TagSchema
from typing import List

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/tags", response_model=List[TagSchema])
def get_tags(db: Session = Depends(get_db)):
    tags = db.query(Tag).all()
    return tags

@router.post("/tags", response_model=TagSchema)
def create_tag(tag: TagSchema, db: Session = Depends(get_db)):
    existing_tag = db.query(Tag).filter(Tag.name == tag.name).first()
    if existing_tag:
        return existing_tag
    new_tag = Tag(name=tag.name)
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag

@router.delete("/tags/{tag_id}", response_model=dict)
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.tag_id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tag)
    db.commit()
    return {"message": "Tag deleted successfully"}