from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import PagePermission, Role
from app.schemas import PagePermissionOut, PagePermissionUpdate

router = APIRouter(prefix="/admin/permissions", tags=["Page Permissions"])


@router.get("/", response_model=List[PagePermissionOut])
def get_all_permissions(db: Session = Depends(get_db)):
    """
    Получить все правила доступа (пути + разрешённые роли).
    """
    return db.query(PagePermission).all()


@router.put("/{permission_id}", response_model=PagePermissionOut)
def update_permission(permission_id: int, permission_data: PagePermissionUpdate, db: Session = Depends(get_db)):
    """
    Обновить список разрешённых ролей для указанного пути.
    """
    # Проверяем, существует ли правило
    db_permission = db.query(PagePermission).filter(PagePermission.id == permission_id).first()
    if not db_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Правило доступа не найдено"
        )

    # Валидация: все role_id из allowed_roles должны существовать в таблице roles
    if permission_data.allowed_roles:
        existing_role_ids = {r.id for r in db.query(Role.id).all()}
        invalid_roles = set(permission_data.allowed_roles) - existing_role_ids
        if invalid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неизвестные ID ролей: {sorted(invalid_roles)}"
            )

    # Обновляем
    db_permission.allowed_roles = permission_data.allowed_roles
    db.commit()
    db.refresh(db_permission)
    return db_permission