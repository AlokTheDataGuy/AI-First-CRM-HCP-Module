"""CRUD endpoints for interactions and HCP lookup."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import HCP, Interaction
from ..schemas import HCPOut, InteractionCreate, InteractionOut

router = APIRouter(prefix="/api", tags=["interactions"])


@router.get("/hcps", response_model=List[HCPOut])
def list_hcps(q: Optional[str] = None, db: Session = Depends(get_db)):
    """List / search HCPs (used by the form's HCP name autocomplete)."""
    query = db.query(HCP)
    if q:
        query = query.filter(HCP.name.ilike(f"%{q}%"))
    return query.order_by(HCP.name).limit(50).all()


@router.get("/interactions", response_model=List[InteractionOut])
def list_interactions(db: Session = Depends(get_db)):
    return db.query(Interaction).order_by(Interaction.id.desc()).limit(100).all()


@router.post("/interactions", response_model=InteractionOut)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)):
    """Persist the form when the user clicks the 'Log' button."""
    record = Interaction(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/interactions/{interaction_id}", response_model=InteractionOut)
def update_interaction(
    interaction_id: int, payload: InteractionCreate, db: Session = Depends(get_db)
):
    record = db.get(Interaction, interaction_id)
    if not record:
        raise HTTPException(status_code=404, detail="Interaction not found")
    for key, value in payload.model_dump().items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record
