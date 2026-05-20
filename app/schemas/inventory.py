from pydantic import BaseModel
from typing import Optional

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