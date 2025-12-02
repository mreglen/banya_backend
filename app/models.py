from sqlalchemy import Column, Float, Integer, String, Text, ForeignKey, DateTime, Boolean, Date, CheckConstraint, func
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import date
from sqlalchemy.dialects.postgresql import ARRAY


class Bath(Base):
    __tablename__ = "baths"

    bath_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    cost = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    base_guests = Column(Integer, nullable=False)
    extra_guest_price = Column(Integer, nullable=False)

    photos = relationship("Photo", back_populates="bath", cascade="all, delete-orphan")
    features = relationship("BathFeature", back_populates="bath", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="bath", cascade="all, delete-orphan")
    reservations = relationship("Reservation", back_populates="bath")


class Photo(Base):
    __tablename__ = "photos"

    photo_id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String(500), nullable=False)

    bath_id = Column(Integer, ForeignKey("baths.bath_id", ondelete="CASCADE"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    bath = relationship("Bath", back_populates="photos")
    product = relationship("Product", back_populates="photos")
    category = relationship("Category", back_populates="photos")


class BathFeature(Base):
    __tablename__ = "bath_features"

    feature_id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), nullable=False)
    value = Column(String(100), nullable=False)
    bath_id = Column(Integer, ForeignKey("baths.bath_id", ondelete="CASCADE"), nullable=False)

    bath = relationship("Bath", back_populates="features")


# Бронирование с сайта
class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, index=True)
    bath_id = Column(Integer, ForeignKey("baths.bath_id"), nullable=False)
    date = Column(Date, nullable=False)
    duration_hours = Column(Integer, nullable=False)
    guests = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bath = relationship("Bath", back_populates="bookings")





# Статусы бронирований
class ReservationStatus(Base):
    __tablename__ = "reservation_status"

    id = Column(Integer, primary_key=True)
    status_name = Column(String(50), nullable=False, unique=True)
    reservations = relationship("Reservation", back_populates="status_rel")


# Основная бронь
class Reservation(Base):
    __tablename__ = 'reservations'

    reservation_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bath_id = Column(Integer, ForeignKey('baths.bath_id'), nullable=False)
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    client_name = Column(String(100), nullable=False)
    client_phone = Column(String(20), nullable=False)
    client_email = Column(String(100))
    notes = Column(Text)
    total_cost = Column(Integer, nullable=False, default=0)
    guests = Column(Integer, nullable=False)
    status_id = Column(Integer, ForeignKey('reservation_status.id'), nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    bath = relationship("Bath", back_populates="reservations")
    status_rel = relationship("ReservationStatus", back_populates="reservations")
    reservation_products = relationship("ReservationProduct", back_populates="reservation", cascade="all, delete-orphan")


# === Компания: Партнёры ===
class Partner(Base):
    __tablename__ = "partners"

    partner_id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(100), nullable=False)
    person_name = Column(String(100), nullable=False)
    partner_inn = Column(String(12), nullable=False)
    partner_phone = Column(String(20), nullable=False)
    partner_email = Column(String(100), nullable=False)


# === Компания: Клиенты ===
class Client(Base):
    __tablename__ = "clients"

    client_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    birth_date = Column(Date, nullable=True)






# === Склад: Категории и товары ===
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("Category", remote_side=[id], back_populates="children")
    products = relationship("Product", back_populates="category")
    photos = relationship("Photo", back_populates="category", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_visible_on_website = Column(Boolean, default=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    total_quantity = Column(Float, default=0)
    last_purchase_price = Column(Float, default=0.0)
    unit_id = Column(Integer, ForeignKey("units_of_measurement.id"), nullable=True)

    category = relationship("Category", back_populates="products")
    photos = relationship("Photo", back_populates="product")
    unit = relationship("UnitOfMeasurement")


class UnitOfMeasurement(Base):
    __tablename__ = "units_of_measurement"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True) 
    description = Column(String(100), nullable=True)


# === Приходные документы ===
class EntranceDocument(Base):
    __tablename__ = "entrance_documents"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, default=date.today)
    supplier_id = Column(Integer, ForeignKey("partners.partner_id"), nullable=False)
    responsible_name = Column(String, nullable=False)
    supplier_number = Column(String, nullable=True)
    total_amount = Column(Float, nullable=False, default=0.0)

    supplier = relationship("Partner", backref="entrance_documents")
    items = relationship("EntranceDocumentItem", back_populates="document", cascade="all, delete-orphan")


class EntranceDocumentItem(Base):
    __tablename__ = "entrance_document_items"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("entrance_documents.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    purchase_price = Column(Float, nullable=False)

    document = relationship("EntranceDocument", back_populates="items")
    product = relationship("Product")


# === Товары в бронировании ===
class ReservationProduct(Base):
    __tablename__ = 'reservation_products'

    reservation_id = Column(Integer, ForeignKey('reservations.reservation_id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)
    quantity = Column(Integer, nullable=False, default=1)

    reservation = relationship("Reservation", back_populates="reservation_products")
    product = relationship("Product")

    def __repr__(self):
        return f"<ReservationProduct reservation_id={self.reservation_id} product_id={self.product_id} qty={self.quantity}>"

# Права доступа


class PagePermission(Base):
    __tablename__ = "page_permissions"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(255), nullable=False, unique=True) 
    title = Column(String(255), nullable=False) 
    allowed_roles = Column(ARRAY(Integer), nullable=False) 

# === Компания: Сотрудники и роли ===



class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)  # <-- ссылка на roles
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

   
    full_name = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String)
    birth_date = Column(Date)

    role_rel = relationship("Role")