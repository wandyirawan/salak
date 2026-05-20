from pydantic import BaseModel
from typing import Optional

class ProductCreate(BaseModel):
    sku: str
    name: str
    unit: str = "pcs"
    price: float = 0
    cost_price: float = 0
    description: str = ""
    category_id: Optional[int] = None
    is_active: bool = True
    images: list = []
    attributes: dict = {}

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None
    images: Optional[list] = None
    attributes: Optional[dict] = None