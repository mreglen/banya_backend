# app/routers/bookings.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app import models, schemas, database

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.post("/", response_model=schemas.BookingOut)
def create_booking(booking: schemas.BookingCreate, db: Session = Depends(database.get_db)):
    try:
        booking_date = datetime.strptime(booking.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Неверный формат даты. Используйте YYYY-MM-DD"
        )

    bath = db.query(models.Bath).filter(models.Bath.bath_id == booking.bath_id).first()
    if not bath:
        raise HTTPException(status_code=404, detail="Баня не найдена")

    db_booking = models.Booking(
        bath_id=booking.bath_id,
        date=booking_date,
        duration_hours=booking.duration_hours,
        guests=booking.guests,
        name=booking.name,
        phone=booking.phone,
        email=booking.email,
        notes=booking.notes,
        is_read=False,
    )

    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    return {
        "booking_id": db_booking.booking_id,
        "bath_id": db_booking.bath_id,
        "date": db_booking.date.strftime("%Y-%m-%d"),
        "duration_hours": db_booking.duration_hours,
        "guests": db_booking.guests,
        "name": db_booking.name,
        "phone": db_booking.phone,
        "email": db_booking.email,
        "notes": db_booking.notes,
        "is_read": db_booking.is_read,
        "created_at": db_booking.created_at.isoformat(),
        "bath": {
            "bath_id": bath.bath_id,
            "name": bath.name,
            "title": bath.title,
            "cost": bath.cost,
            "description": bath.description,
            "photos": [
                {
                    "photo_id": p.photo_id,
                    "image_url": p.image_url,
                    "bath_id": p.bath_id,
                    "massage_id": p.massage_id
                }
                for p in bath.photos
            ],
            "features": [
                {
                    "feature_id": f.feature_id,
                    "key": f.key,
                    "value": f.value
                }
                for f in bath.features
            ],
        }
    }

@router.get("/", response_model=List[schemas.BookingOut])
def get_all_bookings(db: Session = Depends(database.get_db)):
    bookings = db.query(models.Booking).order_by(models.Booking.created_at.desc()).all()
    
    result = []
    for booking in bookings:
        booking_data = {
            "booking_id": booking.booking_id,
            "bath_id": booking.bath_id,
            "date": booking.date.strftime("%Y-%m-%d"),
            "duration_hours": booking.duration_hours,
            "guests": booking.guests,
            "name": booking.name,
            "phone": booking.phone,
            "email": booking.email,
            "notes": booking.notes,
            "is_read": booking.is_read,
            "created_at": booking.created_at.isoformat(),
            "bath": {
                "bath_id": booking.bath.bath_id,
                "name": booking.bath.name,
                "title": booking.bath.title,
                "cost": booking.bath.cost,
                "description": booking.bath.description,
                "photos": [
                    {
                        "photo_id": p.photo_id,
                        "image_url": p.image_url,
                        "bath_id": p.bath_id,
                        "massage_id": p.massage_id
                    }
                    for p in booking.bath.photos
                ],
                "features": [
                    {
                        "feature_id": f.feature_id,
                        "key": f.key,
                        "value": f.value
                    }
                    for f in booking.bath.features
                ],
            } if booking.bath else None,
        }
        result.append(booking_data)
    return result