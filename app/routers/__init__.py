from .health import router as health_router
from .auth import router as auth_router
from .warehouses import router as warehouses_router
from .categories import router as categories_router
from .products import router as products_router
from .inventory import router as inventory_router
from .bulk import router as bulk_router

__all__ = [
    "health_router",
    "auth_router",
    "warehouses_router",
    "categories_router",
    "products_router",
    "inventory_router",
    "bulk_router",
]