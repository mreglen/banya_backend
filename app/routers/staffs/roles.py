from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Role
from app.schemas import RoleCreate, RoleResponse

router = APIRouter(prefix="/admin/company/role", tags=["Roles"])

@router.get("/", response_model=List[RoleResponse])
def get_roles(db: Session = Depends(get_db)):
    return db.query(Role).all()

@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(role_data: RoleCreate, db: Session = Depends(get_db)):
    if db.query(Role).filter(Role.name == role_data.name).first():
        raise HTTPException(status_code=400, detail="Роль с таким именем уже существует")
    db_role = Role(**role_data.dict())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

@router.put("/{id}", response_model=RoleResponse)
def update_role(id: int, role_data: RoleCreate, db: Session = Depends(get_db)):
    db_role = db.query(Role).filter(Role.id == id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    if db.query(Role).filter(Role.name == role_data.name, Role.id != id).first():
        raise HTTPException(status_code=400, detail="Роль с таким именем уже существует")
    db_role.name = role_data.name
    db.commit()
    db.refresh(db_role)
    return db_role

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(id: int, db: Session = Depends(get_db)):
    db_role = db.query(Role).filter(Role.id == id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    db.delete(db_role)
    db.commit()
    return