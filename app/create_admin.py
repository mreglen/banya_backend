import sys
import os

# Добавляем родительскую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User, Role
from app.security import hash_password

DATABASE_URL = "postgresql://postgres:root@localhost/baths_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_admin_user():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            print("❌ Пользователь 'admin' уже существует.")
            return

        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            print("❌ Роль 'admin' не найдена. Убедитесь, что она создана в таблице roles.")
            return

        hashed_password = hash_password("admin")

        admin = User(
            username="admin",
            password_hash=hashed_password,
            role_id=admin_role.id,
            full_name="Администратор",
            is_active=True,
            phone=None,
            email=None,
            birth_date=None
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print(f"✅ Администратор 'admin' успешно добавлен! ID: {admin.user_id}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()