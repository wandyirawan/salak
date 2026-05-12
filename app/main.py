import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Salak Inventory", description="Snake fruit inventory (Python/Granian)")

def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)

# Pydantic Models
class ProductCreate(BaseModel):
    sku: str
    name: str
    unit: str = "pcs"
    attributes: dict = {}

class WarehouseCreate(BaseModel):
    name: str
    location: str = ""

@app.on_event("startup")
def startup():
    logger.info("Running migrations...")
    try:
        from migrate import run_migrations
        run_migrations()
        logger.info("Migrations done.")
    except Exception as e:
        logger.error(f"Migration failed: {e}")

@app.get("/health")
def health():
    return {"status": "ok", "service": "salak"}

@app.get("/db-check")
def db_check():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        conn.close()
        return {"db_status": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Warehouse Endpoints
@app.post("/warehouses")
def create_warehouse(data: WarehouseCreate):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO warehouses (name, location) VALUES (%s, %s) RETURNING *", 
                    (data.name, data.location))
        row = cur.fetchone()
        conn.commit()
        return row
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/warehouses")
def list_warehouses():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM warehouses")
    rows = cur.fetchall()
    conn.close()
    return rows

# Product Endpoints
@app.post("/products")
def create_product(data: ProductCreate):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO products (sku, name, unit, attributes) VALUES (%s, %s, %s, %s) RETURNING *",
                    (data.sku, data.name, data.unit, psycopg2.extras.Json(data.attributes)))
        row = cur.fetchone()
        conn.commit()
        return row
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/products")
def list_products():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    rows = cur.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    import granian
    granian.run("app.main:app", host="0.0.0.0", port=8000, interface="asgi")
