import psycopg2
from psycopg2.extras import RealDictCursor
from .config import settings

def get_db():
    return psycopg2.connect(settings.DATABASE_URL, cursor_factory=RealDictCursor)