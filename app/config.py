from dotenv import load_dotenv
import os
load_dotenv()

class Settings:
    PORT = int(os.getenv("PORT", 8000))
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/salak")
    MANGOSTEEN_URL = os.getenv("MANGOSTEEN_URL", "http://localhost:4000")
    MANGOSTEEN_JWKS_URL = os.getenv("MANGOSTEEN_JWKS_URL", "http://localhost:4000/api/.well-known/jwks.json")
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "pomegranate")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "pomegranate123")
    MINIO_BUCKET = os.getenv("MINIO_BUCKET", "salak-uploads")
    ENV = os.getenv("ENV", "development")

settings = Settings()