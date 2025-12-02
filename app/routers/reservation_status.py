from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas, database

router = APIRouter(
    prefix="/admin/reservation-status",
    tags=["reservation-status"]
)

@router.get("/", response_model=List[schemas.ReservationStatusBase])
def get_reservation_statuses(db: Session = Depends(database.get_db)):
    """
    Получить все возможные статусы бронирований.
    """
    statuses = db.query(models.ReservationStatus).all()
    return statuses