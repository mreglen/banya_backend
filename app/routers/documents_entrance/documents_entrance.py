from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date as dt_date
from app.database import get_db
from app.models import EntranceDocument, EntranceDocumentItem, Product
from app.schemas import EntranceDocumentCreate, EntranceDocumentRead
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/admin/documents/entrance", tags=["Documents - Entrance"])


@router.get("/", response_model=List[EntranceDocumentRead])
def get_documents(db: Session = Depends(get_db)):
    return db.query(EntranceDocument)\
             .options(
                 joinedload(EntranceDocument.supplier),
                 joinedload(EntranceDocument.items).joinedload(EntranceDocumentItem.product)
             )\
             .all()


@router.get("/{doc_id}", response_model=EntranceDocumentRead)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(EntranceDocument)\
             .options(
                 joinedload(EntranceDocument.items).joinedload(EntranceDocumentItem.product)
             )\
             .filter(EntranceDocument.id == doc_id)\
             .first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/", response_model=EntranceDocumentRead, status_code=status.HTTP_201_CREATED)
def create_document(doc: EntranceDocumentCreate, db: Session = Depends(get_db)):
    # Проверка: все product_id существуют
    product_ids = [item.product_id for item in doc.items]
    if not product_ids:
        raise HTTPException(status_code=400, detail="Items are required")

    existing_products = db.query(Product.id).filter(Product.id.in_(product_ids)).all()
    existing_ids = {p.id for p in existing_products}
    if len(existing_ids) != len(set(product_ids)):
        missing = set(product_ids) - existing_ids
        raise HTTPException(status_code=400, detail=f"Products not found: {missing}")

    # Создание документа — БЕЗ items в конструкторе
    db_doc = EntranceDocument(
        date=doc.date,
        supplier_id=doc.supplier_id,
        responsible_name=doc.responsible_name,
        supplier_number=doc.supplier_number,
        total_amount=doc.total_amount,
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # Создание строк и обновление склада
    for item in doc.items:
        # Добавляем строку
        db_item = EntranceDocumentItem(
            document_id=db_doc.id,
            product_id=item.product_id,
            quantity=item.quantity,
            purchase_price=item.purchase_price,
        )
        db.add(db_item)

        # Обновляем товар на складе
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.total_quantity += item.quantity
            product.last_purchase_price = item.purchase_price

    db.commit()
    db.refresh(db_doc)
    return db_doc

@router.put("/{doc_id}", response_model=EntranceDocumentRead)
def update_document(doc_id: int, doc: EntranceDocumentCreate, db: Session = Depends(get_db)):
    db_doc = db.query(EntranceDocument).filter(EntranceDocument.id == doc_id).first()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Обновление полей
    for key, value in doc.model_dump(exclude={"items"}).items():
        setattr(db_doc, key, value)

    # Удаляем старые строки
    db.query(EntranceDocumentItem).filter(EntranceDocumentItem.document_id == doc_id).delete()

    # Добавляем новые
    for item in doc.items:
        db_item = EntranceDocumentItem(
            document_id=doc_id,
            product_id=item.product_id,
            quantity=item.quantity,
            purchase_price=item.purchase_price,
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_doc)
    return db_doc


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    db_doc = db.query(EntranceDocument).filter(EntranceDocument.id == doc_id).first()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(db_doc)
    db.commit()
    return