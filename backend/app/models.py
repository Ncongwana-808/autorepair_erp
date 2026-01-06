from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS - Match PostgreSQL ENUM types
# ============================================================================

class UserRole(str, Enum):
    """User role enum matching database user_role type"""
    admin = "admin"
    worker = "worker"


class JobStatus(str, Enum):
    """Job status enum matching database job_status type"""
    created = "created"
    in_progress = "in_progress"
    waiting_for_parts = "waiting_for_parts"
    completed = "completed"
    cancelled = "cancelled"


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    """Base user schema with common fields"""
    username: str = Field(..., min_length=3, max_length=50)
    role: UserRole


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str


class UserResponse(UserBase):
    """Schema for user response (no password)"""
    id: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Schema for updating user"""
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


# ============================================================================
# CUSTOMER SCHEMAS
# ============================================================================

class CustomerBase(BaseModel):
    """Base customer schema"""
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None


class CustomerCreate(CustomerBase):
    """Schema for creating a customer"""
    pass


class CustomerUpdate(BaseModel):
    """Schema for updating customer"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    """Schema for customer response"""
    id: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# VEHICLE SCHEMAS
# ============================================================================

class VehicleBase(BaseModel):
    """Base vehicle schema"""
    customer_id: int
    make: str = Field(..., min_length=2, max_length=50)
    model: str = Field(..., min_length=1, max_length=50)
    year: int = Field(..., ge=1900, le=2100)
    plate_number: str = Field(..., min_length=2, max_length=20)


class VehicleCreate(VehicleBase):
    """Schema for creating a vehicle"""
    pass


class VehicleUpdate(BaseModel):
    """Schema for updating vehicle"""
    customer_id: Optional[int] = None
    make: Optional[str] = Field(None, min_length=2, max_length=50)
    model: Optional[str] = Field(None, min_length=1, max_length=50)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    plate_number: Optional[str] = Field(None, min_length=2, max_length=20)


class VehicleResponse(VehicleBase):
    """Schema for vehicle response"""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# JOB SCHEMAS
# ============================================================================

class JobBase(BaseModel):
    """Base job schema"""
    vehicle_id: int
    description: str = Field(..., min_length=5)


class JobCreate(JobBase):
    """Schema for creating a job"""
    assigned_worker: Optional[int] = None


class JobUpdate(BaseModel):
    """Schema for updating job"""
    assigned_worker: Optional[int] = None
    description: Optional[str] = Field(None, min_length=5)
    status: Optional[JobStatus] = None


class JobResponse(JobBase):
    """Schema for job response"""
    id: int
    assigned_worker: Optional[int]
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# JOB NOTE SCHEMAS
# ============================================================================

class JobNoteBase(BaseModel):
    """Base job note schema"""
    job_id: int
    note: str = Field(..., min_length=1)


class JobNoteCreate(JobNoteBase):
    """Schema for creating a job note"""
    pass


class JobNoteResponse(JobNoteBase):
    """Schema for job note response"""
    id: int
    worker_id: Optional[int]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# INVOICE SCHEMAS
# ============================================================================

class InvoiceBase(BaseModel):
    """Base invoice schema"""
    job_id: int
    total_amount: float = Field(..., ge=0)


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice"""
    pass


class InvoiceUpdate(BaseModel):
    """Schema for updating invoice"""
    total_amount: Optional[float] = Field(None, ge=0)
    is_paid: Optional[bool] = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response"""
    id: int
    is_paid: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# AUTHENTICATION SCHEMAS
# ============================================================================

class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded JWT token data"""
    user_id: int
    username: str
    role: UserRole