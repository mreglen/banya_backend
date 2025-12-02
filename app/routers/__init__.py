from fastapi import APIRouter
from app.routers.baths import router as baths_router
from app.routers.bookings import router as bookings_router
from app.routers.admin_auth import router as auth_router
from app.routers.admin_reservations import router as reservations
from app.routers.reservation_status import router as reservations_status
from app.routers.partner.partner import router as partner_router
from app.routers.clients.client import router as client_router
from app.routers.staffs.users import router as staff_router
from app.routers.staffs.roles import router as roles_router
from app.routers.products.categories import router as categories_router
from app.routers.products.products import router as products_router
from app.routers.stock.stock_balance import router as stock_router
from app.routers.documents_entrance.documents_entrance import router as documents_entrance_router
from app.routers.staffs.permissions import router as permissions_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(permissions_router)
api_router.include_router(baths_router)

api_router.include_router(bookings_router)
api_router.include_router(reservations)
api_router.include_router(reservations_status)

api_router.include_router(partner_router)
api_router.include_router(client_router)
api_router.include_router(staff_router)
api_router.include_router(roles_router)
api_router.include_router(categories_router)
api_router.include_router(products_router)
api_router.include_router(stock_router)
api_router.include_router(documents_entrance_router)


