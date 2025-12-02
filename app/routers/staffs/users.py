from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, Role
from app.schemas import UserCreate, UserUpdate, UserResponse
from app.security import hash_password

router = APIRouter(prefix="/admin/company/users", tags=["Users"])


@router.get("/", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Проверка уникальности имени пользователя
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")

    # Проверка существования роли
    role = db.query(Role).filter(Role.id == user_data.role_id).first()
    if not role:
        raise HTTPException(status_code=400, detail="Указанная роль не найдена")

    # Хеширование пароля
    hashed_password = hash_password(user_data.password)

    # Создание пользователя
    db_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        phone=user_data.phone,
        email=user_data.email,
        birth_date=user_data.birth_date,
        role_id=user_data.role_id,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Если обновляется роль — проверить её существование
    if user_data.role_id is not None:
        role = db.query(Role).filter(Role.id == user_data.role_id).first()
        if not role:
            raise HTTPException(status_code=400, detail="Указанная роль не найдена")

    # Обновление полей
    update_data = user_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == "password" and value is not None:
            # Хешировать новый пароль
            setattr(db_user, "password_hash", hash_password(value))
        elif key != "password":
            setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    db.delete(db_user)
    db.commit()
    return