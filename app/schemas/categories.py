from pydantic import BaseModel
from typing import Optional

class CategoryCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[int] = None