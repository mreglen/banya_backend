from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from datetime import date


# === Логин ===
class LoginData(BaseModel):
    username: str
    password: str


# === Фото ===
class PhotoBase(BaseModel):
    image_url: str

class PhotoCreate(PhotoBase):
    pass

class PhotoOut(BaseModel):
    photo_id: int
    image_url: str
    bath_id: Optional[int] = None
    # massage_id: Optional[int] = None  <-- УДАЛЕНО

    class Config:
        from_attributes = True


# === Бани ===
class BathFeatureBase(BaseModel):
    key: str
    value: str

class BathFeatureCreate(BathFeatureBase):
    pass

class BathFeatureOut(BathFeatureBase):
    feature_id: int

    class Config:
        from_attributes = True

class BathBase(BaseModel):
    name: str
    title: str
    cost: int
    description: Optional[str] = None
    base_guests: int
    extra_guest_price: int

class BathCreate(BathBase):
    features: List[BathFeatureCreate] = []
    photo_urls: List[str] = []

class BathUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    cost: Optional[int] = None
    description: Optional[str] = None
    base_guests: Optional[int] = None
    extra_guest_price: Optional[int] = None
    photo_urls: Optional[List[str]] = None
    features: Optional[List[BathFeatureCreate]] = None

class BathOut(BathBase):
    bath_id: int
    photos: List[PhotoOut] = []
    features: List[BathFeatureOut] = []

    class Config:
        from_attributes = True


# === Товары в бронировании ===
class ReservationProductCreate(BaseModel):
    product_id: int
    quantity: int = 1

class ReservationProductResponse(BaseModel):
    product_id: int
    name: str
    quantity: int
    purchase_price: float

    class Config:
        from_attributes = True


# === Бронирования (только баня + товары) ===
class ReservationCreate(BaseModel):
    bath_id: int
    start_datetime: str
    end_datetime: str
    client_name: str
    client_phone: str
    client_email: Optional[str] = None
    notes: Optional[str] = None
    guests: int = 1
    status_id: int = 1
    
    products: List[ReservationProductCreate] = []

    class Config:
        from_attributes = True

class ReservationUpdate(BaseModel):
    bath_id: Optional[int] = None
    start_datetime: Optional[str] = None
    end_datetime: Optional[str] = None
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_email: Optional[str] = None
    notes: Optional[str] = None
    guests: Optional[int] = None
    status_id: Optional[int] = None
    
    products: List[ReservationProductCreate] = []   

    class Config:
        from_attributes = True


# Статусы бронирований
class ReservationStatusBase(BaseModel):
    id: int
    status_name: str

    class Config:
        from_attributes = True


class ReservationResponse(BaseModel):
    reservation_id: int
    bath_id: int
    start_datetime: datetime
    end_datetime: datetime
    client_name: str
    client_phone: str
    client_email: Optional[str]
    notes: Optional[str]
    guests: int
    total_cost: int
    status: str
    
    products: List[ReservationProductResponse] = []

    class Config:
        from_attributes = True


# === Заявки с сайта ===
class BookingBase(BaseModel):
    bath_id: int
    date: str
    duration_hours: int
    guests: int
    name: str
    phone: str
    email: Optional[str] = None
    notes: Optional[str] = None

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    is_read: Optional[bool] = None

class BookingOut(BookingBase):
    booking_id: int
    is_read: bool
    created_at: datetime
    bath: BathOut

    class Config:
        from_attributes = True


# === Авторизация / Пользователи ===
class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[date] = None
    role_id: int


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None  # если передан — меняется
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[date] = None
    role_id: Optional[int] = None

    class Config:
        extra = "forbid"  # или используй exclude_unset в вызове


class UserResponse(BaseModel):
    user_id: int
    username: str
    full_name: str
    phone: Optional[str]
    email: Optional[str]
    birth_date: Optional[date]
    role_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# === Партнёры ===
class PartnerBase(BaseModel):
    supplier_name: str
    person_name: str
    partner_inn: str
    partner_phone: str
    partner_email: str

class PartnerCreate(PartnerBase):
    pass

class PartnerUpdate(PartnerBase):
    pass

class PartnerResponse(PartnerBase):
    partner_id: int

    class Config:
        from_attributes = True


# === Клиенты ===
class ClientBase(BaseModel):
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[date] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(ClientBase):
    pass

class ClientResponse(ClientBase):
    client_id: int

    class Config:
        from_attributes = True


# === Сотрудники и роли ===
class StaffBase(BaseModel):
    fullName: str
    phone: Optional[str] = None
    email: Optional[str] = None
    birthDate: Optional[date] = None
    role: str

class StaffCreate(StaffBase):
    pass

class StaffUpdate(StaffBase):
    fullName: Optional[str] = None
    role: Optional[str] = None

class StaffResponse(StaffBase):
    id: int

    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id: int

    class Config:
        from_attributes = True


# === Товары и склад ===
class UnitOfMeasurementBase(BaseModel):
    name: str
    description: Optional[str] = None

class UnitOfMeasurementResponse(UnitOfMeasurementBase):
    id: int

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_visible_on_website: bool = False
    category_id: Optional[int] = None

class ProductCreate(ProductBase):
    unit_id: Optional[int] = None

class ProductPhotoOut(BaseModel):
    photo_id: int
    image_url: str

    class Config:
        from_attributes = True

class Product(ProductBase):
    id: int
    total_quantity: float
    last_purchase_price: float
    unit_id: Optional[int] = None
    photos: List[ProductPhotoOut] = []

    class Config:
        from_attributes = True


# === Категории товаров (для склада) ===
class CategoryBase(BaseModel):
    name: str
    parent_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    photo_urls: Optional[List[str]] = None

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    photo_urls: Optional[List[str]] = None

class Category(CategoryBase):
    id: int
    children: List['Category'] = []
    photos: List[PhotoOut] = []

    class Config:
        from_attributes = True

Category.model_rebuild()


# === Приходные документы ===
class EntranceDocumentItemBase(BaseModel):
    product_id: int
    quantity: int
    purchase_price: float

class EntranceDocumentItemCreate(EntranceDocumentItemBase):
    pass

class EntranceDocumentItemRead(EntranceDocumentItemBase):
    id: int
    product: Product

    class Config:
        from_attributes = True

class EntranceDocumentBase(BaseModel):
    date: date
    supplier_id: int
    responsible_name: str
    supplier_number: Optional[str] = None
    total_amount: float

class EntranceDocumentCreate(EntranceDocumentBase):
    items: List[EntranceDocumentItemCreate]

class EntranceDocumentRead(EntranceDocumentBase):
    id: int
    supplier: PartnerResponse
    items: List[EntranceDocumentItemRead] = []

    class Config:
        from_attributes = True


# === Склад: Товары ===
class StockProduct(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    total_quantity: int = 0
    last_purchase_price: float = 0.0
    unit_id: Optional[int] = None 

    class Config:
        from_attributes = True

# Роли доступа



class PagePermissionBase(BaseModel):
    path: str
    title: str
    allowed_roles: List[int]  

class PagePermissionCreate(PagePermissionBase):
    pass

class PagePermissionUpdate(BaseModel):
    allowed_roles: List[int]

class PagePermissionOut(PagePermissionBase):
    id: int

    class Config:
        from_attributes = True