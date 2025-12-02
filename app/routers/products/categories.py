from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from pathlib import Path
from app.database import get_db
from app.models import Category, Photo
from app.schemas import Category as CategorySchema, CategoryCreate, CategoryUpdate

router = APIRouter(prefix="/admin/categories", tags=["categories"])

UPLOAD_DIR = Path("public/img/categories/")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/", response_model=List[CategorySchema])
def read_categories(db: Session = Depends(get_db)):
    categories = db.query(Category)\
        .options(joinedload(Category.photos))\
        .filter(Category.parent_id.is_(None))\
        .all()
    return categories


@router.get("/{category_id}", response_model=CategorySchema)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category)\
        .options(joinedload(Category.photos))\
        .filter(Category.id == category_id)\
        .first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("/", response_model=CategorySchema, status_code=201)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = Category(
        name=category.name,
        parent_id=category.parent_id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    # Добавляем фото из photo_urls
    if category.photo_urls:
        for url in category.photo_urls:
            db_photo = Photo(image_url=url, category=db_category)
            db.add(db_photo)
        db.commit()
        db.refresh(db_category)

    return db_category


@router.put("/{category_id}", response_model=CategorySchema)
def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    db: Session = Depends(get_db)
):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Обновляем основные поля
    update_data = category_update.model_dump(exclude_unset=True)
    for field in ["name", "parent_id"]:
        if field in update_data:
            value = update_data[field]
            # Защита от циклической ссылки
            if field == "parent_id" and value == category_id:
                raise HTTPException(status_code=400, detail="Cannot set self as parent")
            setattr(db_category, field, value)

    # Обработка фото: если photo_urls передан — заменяем все
    if category_update.photo_urls is not None:
        db.query(Photo).filter(Photo.category_id == category_id).delete()
        for url in category_update.photo_urls:
            db_photo = Photo(image_url=url, category=db_category)
            db.add(db_photo)

    db.commit()
    db.refresh(db_category)
    return db_category


@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if category.children:
        raise HTTPException(status_code=400, detail="Cannot delete category with subcategories")
    if category.products:
        raise HTTPException(status_code=400, detail="Cannot delete category with products")
    db.delete(category)
    db.commit()
    return {"ok": True}


@router.post("/{category_id}/upload", response_model=List[str])
async def upload_category_photos(
    category_id: int,
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db)
):
    # Проверка существования категории
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Удаляем все существующие фото
    db.query(Photo).filter(Photo.category_id == category_id).delete()

    urls = []
    if files:  # ← только если файлы переданы
        for file in files:
            filename = f"{category_id}_{file.filename.replace(' ', '_').replace('/', '_')}"
            filepath = UPLOAD_DIR / filename
            content = await file.read()
            with open(filepath, "wb") as f:
                f.write(content)
            url = f"/img/categories/{filename}"
            db_photo = Photo(image_url=url, category=db_category)
            db.add(db_photo)
            urls.append(url)

    db.commit()
    return urls