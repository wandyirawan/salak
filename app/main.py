import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Salak Inventory", description="Snake fruit inventory (Python/Granian)")

def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)

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

if __name__ == "__main__":
    import granian
    granian.run("app.main:app", host="0.0.0.0", port=8000, interface="asgi")
