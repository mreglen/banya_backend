from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Partner
from app.schemas import PartnerCreate, PartnerUpdate, PartnerResponse

router = APIRouter(prefix="/admin/company/partner", tags=["Partners"])

@router.get("/", response_model=List[PartnerResponse])
def get_partners(db: Session = Depends(get_db)):
    return db.query(Partner).all()

@router.get("/{partner_id}", response_model=PartnerResponse)
def get_partner(partner_id: int, db: Session = Depends(get_db)):
    partner = db.query(Partner).filter(Partner.partner_id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Партнёр не найден")
    return partner

@router.post("/", response_model=PartnerResponse, status_code=status.HTTP_201_CREATED)
def create_partner(partner_data: PartnerCreate, db: Session = Depends(get_db)):
    db_partner = Partner(**partner_data.dict())
    db.add(db_partner)
    db.commit()
    db.refresh(db_partner)
    return db_partner

@router.put("/{partner_id}", response_model=PartnerResponse)
def update_partner(partner_id: int, partner_data: PartnerUpdate, db: Session = Depends(get_db)):
    db_partner = db.query(Partner).filter(Partner.partner_id == partner_id).first()
    if not db_partner:
        raise HTTPException(status_code=404, detail="Партнёр не найден")
    
    for key, value in partner_data.dict(exclude_unset=True).items():
        setattr(db_partner, key, value)
    
    db.commit()
    db.refresh(db_partner)
    return db_partner

@router.delete("/{partner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_partner(partner_id: int, db: Session = Depends(get_db)):
    db_partner = db.query(Partner).filter(Partner.partner_id == partner_id).first()
    if not db_partner:
        raise HTTPException(status_code=404, detail="Партнёр не найден")
    db.delete(db_partner)
    db.commit()
    return