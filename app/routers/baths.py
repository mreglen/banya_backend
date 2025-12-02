from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import os
from pathlib import Path
from app.database import get_db
from app.models import Bath, Photo, BathFeature
from app.schemas import BathOut, BathCreate, BathUpdate

router = APIRouter(prefix="/baths", tags=["baths"])


@router.get("/")
def get_baths(db: Session = Depends(get_db)):

    baths = db.query(Bath)\
        .options(joinedload(Bath.photos))\
        .options(joinedload(Bath.features))\
        .all()

    if not baths:
        return []

    return baths


@router.get("/{bath_id}")
def get_bath(bath_id: int, db: Session = Depends(get_db)):
    bath = db.query(Bath)\
        .options(joinedload(Bath.photos))\
        .options(joinedload(Bath.features))\
        .filter(Bath.bath_id == bath_id)\
        .first()

    if not bath:
        raise HTTPException(status_code=404, detail="Баня не найдена")

    return {
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
                "value": f.value,
                "bath_id": f.bath_id
            }
            for f in bath.features
        ]
    }

# новые эндпоинты
@router.post("/", response_model=BathOut, status_code=201)
def create_bath(
    bath: BathCreate,
    db: Session = Depends(get_db)
):
    # Создаём баню
    db_bath = Bath(
        name=bath.name,
        title=bath.title,
        cost=bath.cost,
        description=bath.description,
    )
    db.add(db_bath)
    db.commit()
    db.refresh(db_bath)

    # Добавляем фото
    for url in bath.photo_urls:
        db_photo = Photo(image_url=url, bath=db_bath)
        db.add(db_photo)

    # Добавляем особенности
    for feature in bath.features:
        db_feature = BathFeature(key=feature.key, value=feature.value, bath=db_bath)
        db.add(db_feature)

    db.commit()
    db.refresh(db_bath)
    return db_bath


@router.put("/{bath_id}", response_model=BathOut)
def update_bath(
    bath_id: int,
    bath_update: BathUpdate,
    db: Session = Depends(get_db)
):
    db_bath = db.query(Bath).filter(Bath.bath_id == bath_id).first()
    if not db_bath:
        raise HTTPException(status_code=404, detail="Баня не найдена")

    # Обновляем основные поля
    for key, value in bath_update.model_dump(exclude_unset=True).items():
        if key not in ["photo_urls", "features"]:
            setattr(db_bath, key, value)

    # Обработка фото: если передано — заменяем все
    if bath_update.photo_urls is not None:
        # Удаляем старые
        db.query(Photo).filter(Photo.bath_id == bath_id).delete()
        # Добавляем новые
        for url in bath_update.photo_urls:
            db_photo = Photo(image_url=url, bath=db_bath)
            db.add(db_photo)

    # Обработка особенностей: если передано — заменяем все
    if bath_update.features is not None:
        # Удаляем старые
        db.query(BathFeature).filter(BathFeature.bath_id == bath_id).delete()
        # Добавляем новые
        for feature in bath_update.features:
            db_feature = BathFeature(key=feature.key, value=feature.value, bath=db_bath)
            db.add(db_feature)

    db.commit()
    db.refresh(db_bath)
    return db_bath


@router.delete("/{bath_id}", status_code=204)
def delete_bath(bath_id: int, db: Session = Depends(get_db)):
    db_bath = db.query(Bath).filter(Bath.bath_id == bath_id).first()
    if not db_bath:
        raise HTTPException(status_code=404, detail="Баня не найдена")
    
    db.delete(db_bath)
    db.commit()
    return None

# добавить фото
UPLOAD_DIR = Path("public/img/baths/")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/{bath_id}/upload", response_model=List[str])
async def upload_bath_photos(
    bath_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    db_bath = db.query(Bath).filter(Bath.bath_id == bath_id).first()
    if not db_bath:
        raise HTTPException(status_code=404, detail="Баня не найдена")

    # Удаляем старые фото (если хотите заменять)
    db.query(Photo).filter(Photo.bath_id == bath_id).delete()

    urls = []
    for file in files:
        # Генерируем уникальное имя файла
        extension = file.filename.split('.')[-1]
        unique_filename = f"{bath_id}_{file.filename.replace(' ', '_')}"
        filepath = UPLOAD_DIR / unique_filename

        # Сохраняем файл
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)

        # Сохраняем URL в базу
        db_photo = Photo(image_url=f"/img/baths/{unique_filename}", bath=db_bath)
        db.add(db_photo)
        urls.append(f"/img/baths/{unique_filename}")

    db.commit()
    return urls