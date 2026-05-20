import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .config import settings
from .routers import (
    health_router,
    auth_router,
    warehouses_router,
    categories_router,
    products_router,
    inventory_router,
    bulk_router,
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Salak Inventory",
    description="Snake fruit inventory (Python/Granian)",
)

# CORS — allow Pome (Bun/Elysia) frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4021", "http://127.0.0.1:4021"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with path prefixes
app.include_router(health_router)
app.include_router(auth_router)  # /auth/login (prefix handled inside router)
app.include_router(warehouses_router, prefix="/warehouses")
app.include_router(categories_router, prefix="/categories")
app.include_router(products_router, prefix="/products")
app.include_router(inventory_router)  # stock-in, stock-out, inventory, transactions
app.include_router(bulk_router)  # /products/template, /products/bulk-upload

# Startup: run migrations
@app.on_event("startup")
def startup():
    logger.info("Running migrations...")
    try:
        from migrate import run_migrations
        run_migrations()
        logger.info("Migrations done.")
    except Exception as e:
        logger.error(f"Migration failed: {e}")