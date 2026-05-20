from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from ..config import settings

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/auth/login")
def proxy_login(data: LoginRequest):
    """Proxy login to Mangosteen, return JWT for subsequent Salak API calls."""
    try:
        mangosteen = settings.MANGOSTEEN_URL
        resp = requests.post(
            f"{mangosteen}/api/auth/login",
            json={"email": data.email, "password": data.password},
            timeout=10,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Mangosteen unreachable: {e}")