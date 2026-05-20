import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .config import settings
from .routers import health, auth, warehouses, categories, products, inventory, bulk

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

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(warehouses.router, prefix="/warehouses", tags=["warehouses"])
app.include_router(categories.router, prefix="/categories", tags=["categories"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(inventory.router, tags=["inventory"])
app.include_router(bulk.router, tags=["products"])  # bulk shares /products prefix

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