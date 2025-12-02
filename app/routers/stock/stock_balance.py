from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product as ProductModel 
from app.schemas import StockProduct

router = APIRouter(prefix="/admin/stock", tags=["stock"])

@router.get("/products", response_model=list[StockProduct])
def get_stock_products(db: Session = Depends(get_db)):
    return db.query(ProductModel).all()