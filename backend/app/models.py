from pydantic import BaseModel
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

    class Config:
        orm_mode = True