from pydantic import BaseModel ,ConfigDict
from typing import Optional


class CustomerCreate(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class CustomerResponse(BaseModel):
    id: int
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

model_config = ConfigDict(from_attributes=True) # Enable ORM mode for Pydantic v2 