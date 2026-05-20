from pydantic import BaseModel
from typing import Optional

class WarehouseCreate(BaseModel):
    name: str
    location: str = ""

class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None