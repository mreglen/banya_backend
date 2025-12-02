from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime, timedelta
from app import models, schemas, database
from app.auth import get_current_user


router = APIRouter(
    prefix="/admin/reservations",
    tags=["reservations"]
)


def check_overlap(db: Session, bath_id: int, start: datetime, end: datetime, exclude_id: int = None):
    """
    Проверяет пересечение с существующими бронями, включая 30-минутную уборку после каждой.
    Уборка = end_datetime + 30 минут.
    """
    query = db.query(models.Reservation).filter(
        models.Reservation.bath_id == bath_id,
        models.Reservation.start_datetime < end,
        (models.Reservation.end_datetime + timedelta(minutes=30)) > start
    )
    if exclude_id:
        query = query.filter(models.Reservation.reservation_id != exclude_id)
    return query.first()


@router.get("/", response_model=List[schemas.ReservationResponse])
def get_reservations(
    date: str = None, 
    bath_id: int = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Reservation).options(
        joinedload(models.Reservation.status_rel),
        joinedload(models.Reservation.reservation_products).joinedload(models.ReservationProduct.product)
    )

    if date is not None:
        try:
            if "T" in date:
                target_date = datetime.fromisoformat(date.split('T')[0]).date()
            else:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        query = query.filter(
            models.Reservation.start_datetime >= start_of_day,
            models.Reservation.end_datetime <= end_of_day
        )

    if bath_id is not None:
        query = query.filter(models.Reservation.bath_id == bath_id)

    reservations = query.all()

    for res in reservations:
        # Товары — только если объект существует
        res.products = [
            schemas.ReservationProductResponse(
                product_id=rp.product.id,
                name=rp.product.name,
                quantity=rp.quantity,
                purchase_price=rp.product.last_purchase_price
            )
            for rp in res.reservation_products
            if rp.product is not None
        ]
        
        # Статус
        res.status = res.status_rel.status_name if res.status_rel else "Неизвестный"

    return reservations


@router.post("/", response_model=schemas.ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(
    reservation: schemas.ReservationCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Проверяем, существует ли баня
    bath = db.query(models.Bath).filter(models.Bath.bath_id == reservation.bath_id).first()
    if not bath:
        raise HTTPException(status_code=404, detail="Баня не найдена")

    # 2. Проверяем, существует ли статус
    status_obj = db.query(models.ReservationStatus).filter(models.ReservationStatus.id == reservation.status_id).first()
    if not status_obj:
        raise HTTPException(status_code=400, detail=f"Статус с ID {reservation.status_id} не найден")

    # 3. Парсим даты
    try:
        start_dt = datetime.fromisoformat(reservation.start_datetime)
        end_dt = datetime.fromisoformat(reservation.end_datetime)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты. Используйте ISO: YYYY-MM-DDTHH:MM:SS")

    if start_dt >= end_dt:
        raise HTTPException(status_code=400, detail="Время окончания должно быть позже начала")

    # 4. Проверяем пересечения
    overlap = check_overlap(db, reservation.bath_id, start_dt, end_dt)
    if overlap:
        raise HTTPException(status_code=400, detail="Бронь пересекается с существующей")

    # 5. Рассчитываем общую стоимость
    total_cost = 0

    # 5.1 Стоимость бани + гости
    duration_hours = (end_dt - start_dt).total_seconds() / 3600
    bath_base_cost = int(bath.cost * duration_hours)
    extra_guests = max(0, reservation.guests - bath.base_guests)
    extra_guest_cost = extra_guests * bath.extra_guest_price
    total_cost += bath_base_cost + extra_guest_cost

    # 5.2 Стоимость товаров
    if reservation.products:
        product_ids = [p.product_id for p in reservation.products]
        products = db.query(models.Product).filter(models.Product.id.in_(product_ids)).all()
        product_map = {p.id: p for p in products}
        for item in reservation.products:
            product = product_map.get(item.product_id)
            if not product:
                raise HTTPException(status_code=400, detail=f"Товар с ID {item.product_id} не найден")
            if product.total_quantity < item.quantity:
                raise HTTPException(status_code=400, detail=f"Недостаточно товара {product.name} на складе")
            total_cost += product.last_purchase_price * item.quantity

    # 6. Создаём бронь
    db_reservation = models.Reservation(
        bath_id=reservation.bath_id,
        start_datetime=start_dt,
        end_datetime=end_dt,
        client_name=reservation.client_name,
        client_phone=reservation.client_phone,
        client_email=reservation.client_email,
        notes=reservation.notes,
        guests=reservation.guests,
        total_cost=total_cost,
        status_id=reservation.status_id,
    )
    db.add(db_reservation)
    db.flush()

    # 7. Сохраняем товары и списываем со склада
    if reservation.products:
        for item in reservation.products:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=400, detail=f"Товар с ID {item.product_id} не найден")
            if product.total_quantity < item.quantity:
                raise HTTPException(status_code=400, detail=f"Недостаточно товара {product.name} на складе")
            product.total_quantity -= item.quantity
            db.add(models.ReservationProduct(
                reservation_id=db_reservation.reservation_id,
                product_id=item.product_id,
                quantity=item.quantity
            ))

    db.commit()
    db.refresh(db_reservation)

    # === ФОРМИРУЕМ ОТВЕТ ВРУЧНУЮ ===
    response_products = []
    if reservation.products:
        for item in reservation.products:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if product:
                response_products.append(
                    schemas.ReservationProductResponse(
                        product_id=product.id,
                        name=product.name,
                        quantity=item.quantity,
                        purchase_price=product.last_purchase_price
                    )
                )

    return schemas.ReservationResponse(
        reservation_id=db_reservation.reservation_id,
        bath_id=db_reservation.bath_id,
        start_datetime=db_reservation.start_datetime,
        end_datetime=db_reservation.end_datetime,
        client_name=db_reservation.client_name,
        client_phone=db_reservation.client_phone,
        client_email=db_reservation.client_email,
        notes=db_reservation.notes,
        guests=db_reservation.guests,
        total_cost=db_reservation.total_cost,
        status=status_obj.status_name,
        products=response_products,
        # Поле `massages` отсутствует в схеме ReservationResponse (см. schemas.py)
    )


@router.get("/{id}", response_model=schemas.ReservationResponse)
def get_reservation(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    reservation = db.query(models.Reservation)\
        .options(
            joinedload(models.Reservation.status_rel),
            joinedload(models.Reservation.reservation_products).joinedload(models.ReservationProduct.product)
        )\
        .filter(models.Reservation.reservation_id == id)\
        .first()
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Бронь не найдена")

    reservation.products = [
        schemas.ReservationProductResponse(
            product_id=rp.product.id,
            name=rp.product.name,
            quantity=rp.quantity,
            purchase_price=rp.product.last_purchase_price
        )
        for rp in reservation.reservation_products
    ]
    reservation.status = reservation.status_rel.status_name

    return reservation


@router.put("/{id}", response_model=schemas.ReservationResponse)
def update_reservation(
    id: int,
    reservation: schemas.ReservationUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_reservation = db.query(models.Reservation).filter(models.Reservation.reservation_id == id).first()
    if not db_reservation:
        raise HTTPException(status_code=404, detail="Бронь не найдена")

    # === ВОЗВРАТ СТАРЫХ ТОВАРОВ НА СКЛАД ===
    old_products = db.query(models.ReservationProduct).filter(models.ReservationProduct.reservation_id == id).all()
    for old_rp in old_products:
        product = db.query(models.Product).filter(models.Product.id == old_rp.product_id).first()
        if product:
            product.total_quantity += old_rp.quantity

    # Обновляем основные поля
    update_data = reservation.model_dump(
        exclude={"guests", "status_id", "products"},
        exclude_unset=True
    )
    for key, value in update_data.items():
        if value is not None:
            setattr(db_reservation, key, value)

    # Обработка guests
    current_guests = reservation.guests if reservation.guests is not None else db_reservation.guests
    db_reservation.guests = current_guests

    # Обработка status_id
    status_obj = None
    if reservation.status_id is not None:
        status_obj = db.query(models.ReservationStatus).filter(models.ReservationStatus.id == reservation.status_id).first()
        if not status_obj:
            raise HTTPException(status_code=400, detail=f"Статус с ID {reservation.status_id} не найден")
        db_reservation.status_id = reservation.status_id

    # Обработка дат
    start_dt = db_reservation.start_datetime
    end_dt = db_reservation.end_datetime

    if reservation.start_datetime:
        try:
            start_dt = datetime.fromisoformat(reservation.start_datetime)
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный формат даты начала")
    if reservation.end_datetime:
        try:
            end_dt = datetime.fromisoformat(reservation.end_datetime)
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный формат даты окончания")

    if start_dt >= end_dt:
        raise HTTPException(status_code=400, detail="Время окончания должно быть позже начала")

    # Проверка пересечений
    overlap = check_overlap(db, db_reservation.bath_id, start_dt, end_dt, exclude_id=id)
    if overlap:
        raise HTTPException(status_code=400, detail="Бронь пересекается с существующей")

    db_reservation.start_datetime = start_dt
    db_reservation.end_datetime = end_dt

    # Пересчёт стоимости
    bath = db.query(models.Bath).filter(models.Bath.bath_id == db_reservation.bath_id).first()
    if not bath:
        raise HTTPException(status_code=500, detail="Баня, связанная с бронью, не найдена")

    duration_hours = (end_dt - start_dt).total_seconds() / 3600
    bath_base_cost = int(bath.cost * duration_hours)
    extra_guests = max(0, current_guests - bath.base_guests)
    extra_guest_cost = extra_guests * bath.extra_guest_price
    total_cost = bath_base_cost + extra_guest_cost

    # Стоимость товаров
    if reservation.products:
        product_ids = [p.product_id for p in reservation.products]
        products = db.query(models.Product).filter(models.Product.id.in_(product_ids)).all()
        product_map = {p.id: p for p in products}
        for item in reservation.products:
            product = product_map.get(item.product_id)
            if not product:
                raise HTTPException(status_code=400, detail=f"Товар с ID {item.product_id} не найден")
            if product.total_quantity < item.quantity:
                raise HTTPException(status_code=400, detail=f"Недостаточно товара {product.name} на складе")
            total_cost += product.last_purchase_price * item.quantity

    db_reservation.total_cost = total_cost

    # Удаляем старые связи (только товары)
    db.query(models.ReservationProduct).filter(models.ReservationProduct.reservation_id == id).delete()

    # Добавляем новые товары и списываем их
    if reservation.products:
        for item in reservation.products:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=400, detail=f"Товар с ID {item.product_id} не найден")
            if product.total_quantity < item.quantity:
                raise HTTPException(status_code=400, detail=f"Недостаточно товара {product.name} на складе")
            product.total_quantity -= item.quantity
            db.add(models.ReservationProduct(
                reservation_id=id,
                product_id=item.product_id,
                quantity=item.quantity
            ))

    db.commit()
    db.refresh(db_reservation)

    # === ФОРМИРУЕМ ОТВЕТ ВРУЧНУЮ ===
    response_products = []
    if reservation.products:
        for item in reservation.products:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if product:
                response_products.append(
                    schemas.ReservationProductResponse(
                        product_id=product.id,
                        name=product.name,
                        quantity=item.quantity,
                        purchase_price=product.last_purchase_price
                    )
                )

    status_name = (status_obj or db.query(models.ReservationStatus)
                   .filter(models.ReservationStatus.id == db_reservation.status_id)
                   .first()).status_name

    return schemas.ReservationResponse(
        reservation_id=db_reservation.reservation_id,
        bath_id=db_reservation.bath_id,
        start_datetime=db_reservation.start_datetime,
        end_datetime=db_reservation.end_datetime,
        client_name=db_reservation.client_name,
        client_phone=db_reservation.client_phone,
        client_email=db_reservation.client_email,
        notes=db_reservation.notes,
        guests=db_reservation.guests,
        total_cost=db_reservation.total_cost,
        status=status_name,
        products=response_products,
        # Поле `massages` отсутствует
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reservation(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    reservation = db.query(models.Reservation).filter(models.Reservation.reservation_id == id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Бронь не найдена")

    # === ВОЗВРАТ ТОВАРОВ НА СКЛАД ДО УДАЛЕНИЯ ===
    for rp in reservation.reservation_products:
        product = db.query(models.Product).filter(models.Product.id == rp.product_id).first()
        if product:
            product.total_quantity += rp.quantity

    # Теперь можно безопасно удалить
    db.delete(reservation)
    db.commit()

    return None