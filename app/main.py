import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
import logging
import jwt
import requests
from jwt.algorithms import RSAAlgorithm

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Salak Inventory", description="Snake fruit inventory (Python/Granian)")

# JWT Setup
security = HTTPBearer()
_jwks_cache = None

def get_jwks():
    global _jwks_cache
    if not _jwks_cache:
        url = os.getenv("MANGOSTEEN_JWKS_URL")
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        _jwks_cache = resp.json()
    return _jwks_cache

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        jwks = get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header["kid"]
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Invalid token key")
        public_key = RSAAlgorithm.from_jwk(key)
        payload = jwt.decode(token, public_key, algorithms=["RS256"], audience="mangosteen")
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

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

class StockIn(BaseModel):
    product_id: int
    warehouse_id: int
    quantity: float
    reference_id: str = ""
    notes: str = ""

class StockOut(BaseModel):
    product_id: int
    warehouse_id: int
    quantity: float
    reference_id: str = ""
    notes: str = ""

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
def list_warehouses(user: dict = Depends(verify_token)):
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
def list_products(user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    rows = cur.fetchall()
    conn.close()
    return rows

# Stock Endpoints
@app.post("/stock-in")
def stock_in(data: StockIn, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO inventory_transactions (product_id, warehouse_id, delta_qty, reference_id, notes) VALUES (%s, %s, %s, %s, %s) RETURNING *",
                    (data.product_id, data.warehouse_id, data.quantity, data.reference_id, data.notes))
        row = cur.fetchone()
        conn.commit()
        return row
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/stock-out")
def stock_out(data: StockOut, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    try:
        # Check real_qty
        cur.execute("SELECT real_qty FROM inventory WHERE product_id=%s AND warehouse_id=%s", 
                    (data.product_id, data.warehouse_id))
        row = cur.fetchone()
        if not row or row['real_qty'] < data.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        
        cur.execute("INSERT INTO inventory_transactions (product_id, warehouse_id, delta_qty, reference_id, notes) VALUES (%s, %s, %s, %s, %s) RETURNING *",
                    (data.product_id, data.warehouse_id, -abs(data.quantity), data.reference_id, data.notes))
        row = cur.fetchone()
        conn.commit()
        return row
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/inventory")
def check_inventory(product_id: int = None, warehouse_id: int = None):
    conn = get_db()
    cur = conn.cursor()
    if product_id and warehouse_id:
        cur.execute("SELECT * FROM inventory WHERE product_id=%s AND warehouse_id=%s", (product_id, warehouse_id))
    elif product_id:
        cur.execute("SELECT * FROM inventory WHERE product_id=%s", (product_id,))
    else:
        cur.execute("SELECT * FROM inventory")
    rows = cur.fetchall()
    conn.close()
    return rows

@app.get("/inventory/check")
def check_by_sku(sku: str, warehouse_id: int = None, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM products WHERE sku=%s", (sku,))
    prod = cur.fetchone()
    if not prod:
        raise HTTPException(status_code=404, detail="SKU not found")
    
    if warehouse_id:
        cur.execute("SELECT * FROM inventory WHERE product_id=%s AND warehouse_id=%s", (prod['id'], warehouse_id))
    else:
        cur.execute("SELECT * FROM inventory WHERE product_id=%s", (prod['id'],))
    
    rows = cur.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    import granian
    granian.run("app.main:app", host="0.0.0.0", port=8000, interface="asgi")
