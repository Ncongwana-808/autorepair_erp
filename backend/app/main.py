"""
main.py - FastAPI Application Entry Point

This is the heart of your API where all routes are defined.

STRUCTURE:
1. HTML page serving
2. Authentication routes (register, login)
3. User management routes (admin only)
4. Customer routes
5. Vehicle routes
6. Job routes
7. Job notes routes
8. Invoice routes
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional
import os


app = FastAPI(
    title="Auto Repair Workshop ERP",
    description="Backend API for managing auto repair workshop operations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import models
from models import (
    UserCreate, UserLogin, UserResponse, UserUpdate,
    CustomerCreate, CustomerResponse, CustomerUpdate,
    VehicleCreate, VehicleResponse, VehicleUpdate,
    JobCreate, JobResponse, JobUpdate,
    JobNoteCreate, JobNoteResponse,
    InvoiceCreate, InvoiceResponse, InvoiceUpdate,
    Token
)

# Import database functions
from database import get_db, close_db_connection

# Import query functions
from queries import (
    create_user, get_user_by_username, get_user_by_id, update_user, get_all_users,
    create_customer, get_customer_by_id, get_all_customers, update_customer,
    create_vehicle, get_vehicle_by_id, get_vehicles_by_customer, get_all_vehicles,
    create_job, get_job_by_id, get_jobs_by_worker, get_all_jobs, update_job,
    create_job_note, get_notes_by_job,
    create_invoice, get_invoice_by_job, update_invoice, get_all_invoices
)

# Import auth functions
from auth import (
    hash_password, authenticate_user, create_token_response,
    get_current_user, get_current_active_admin, get_current_active_worker
)

# ============================================================================
# CONFIGURE FRONTEND PATH
# ============================================================================

# Get the directory where main.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up to backend, then to frontend folder
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "..", "frontend")

# Make frontend directory absolute path
FRONTEND_DIR = os.path.abspath(FRONTEND_DIR)

print(f"Frontend directory: {FRONTEND_DIR}")


# ============================================================================
# HTML PAGE ROUTES
# ============================================================================

@app.get("/", tags=["Frontend"])
def serve_login_page():
    """Serve login page as root"""
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))


@app.get("/login", tags=["Frontend"])
def serve_login():
    """Serve login page"""
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))


@app.get("/register", tags=["Frontend"])
def serve_register():
    """Serve registration page"""
    return FileResponse(os.path.join(FRONTEND_DIR, "register.html"))


@app.get("/dashboard", tags=["Frontend"])
def serve_dashboard():
    """Serve dashboard page"""
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))


@app.get("/customers", tags=["Frontend"])
def serve_customers_page():
    """Serve customers page"""
    return FileResponse(os.path.join(FRONTEND_DIR, "customers.html"))


@app.get("/vehicles", tags=["Frontend"])
def serve_vehicles_page():
    """Serve vehicles page"""
    return FileResponse(os.path.join(FRONTEND_DIR, "vehicles.html"))


@app.get("/jobs", tags=["Frontend"])
def serve_jobs_page():
    """Serve jobs page"""
    return FileResponse(os.path.join(FRONTEND_DIR, "jobs.html"))


@app.get("/invoices", tags=["Frontend"])
def serve_invoices_page():
    """Serve invoices page"""
    return FileResponse(os.path.join(FRONTEND_DIR, "invoices.html"))


# ============================================================================
# API INFO ENDPOINT
# ============================================================================

@app.get("/api", tags=["API Info"])
def api_info():
    """API information endpoint"""
    return {
        "message": "Welcome to the Auto Repair Workshop Management System API",
        "version": "1.0.0",
        "docs": "/docs",  # Swagger UI
        "redoc": "/redoc"  # ReDoc UI
    }


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
def register_user(user_data: UserCreate):
    """
    Register a new user (admin or worker).
    
    HOW IT WORKS:
    1. Receive username, password, and role
    2. Check if username already exists
    3. Hash the password (never store plain passwords!)
    4. Create user in database
    5. Return JWT token for immediate login
    
    Example request body:
    {
        "username": "john_worker",
        "password": "securePassword123",
        "role": "worker"
    }
    """
    conn = get_db()
    
    try:
        # Check if username already exists
        existing_user = get_user_by_username(conn, user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Hash the password
        password_hash = hash_password(user_data.password)
        
        # Create the user
        new_user = create_user(conn, user_data.username, password_hash, user_data.role.value)
        
        if not new_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Return token for immediate login
        return create_token_response(new_user)
    
    finally:
        close_db_connection(conn)


@app.post("/auth/login", response_model=Token, tags=["Authentication"])
def login(credentials: UserLogin):
    """
    Login endpoint - Get JWT token.
    
    Example request:
    {
        "username": "john_worker",
        "password": "securePassword123"
    }
    """
    user = authenticate_user(credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return create_token_response(user)


@app.get("/auth/me", response_model=UserResponse, tags=["Authentication"])
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user's information."""
    return UserResponse(**current_user)


# ============================================================================
# USER MANAGEMENT ENDPOINTS (ADMIN ONLY)
# ============================================================================

@app.get("/api/users", response_model=List[UserResponse], tags=["Users"])
def list_all_users(admin: dict = Depends(get_current_active_admin)):
    """Get all users in the system. ADMIN ONLY."""
    conn = get_db()
    try:
        users = get_all_users(conn)
        return [UserResponse(**user) for user in users]
    finally:
        close_db_connection(conn)


@app.get("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
def get_user(user_id: int, admin: dict = Depends(get_current_active_admin)):
    """Get a specific user by ID. ADMIN ONLY."""
    conn = get_db()
    try:
        user = get_user_by_id(conn, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserResponse(**user)
    finally:
        close_db_connection(conn)


@app.patch("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
def update_user_info(
    user_id: int,
    user_update: UserUpdate,
    admin: dict = Depends(get_current_active_admin)
):
    """Update user information. ADMIN ONLY."""
    conn = get_db()
    try:
        updated_user = update_user(
            conn,
            user_id,
            role=user_update.role.value if user_update.role else None,
            is_active=user_update.is_active
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or no changes made"
            )
        
        return UserResponse(**updated_user)
    finally:
        close_db_connection(conn)


# ============================================================================
# CUSTOMER ENDPOINTS (WORKER + ADMIN)
# ============================================================================

@app.post("/api/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED, tags=["Customers"])
def create_new_customer(
    customer_data: CustomerCreate,
    current_user: dict = Depends(get_current_active_worker)
):
    """Create a new customer."""
    conn = get_db()
    try:
        new_customer = create_customer(
            conn,
            customer_data.full_name,
            customer_data.phone,
            customer_data.email,
            customer_data.address
        )
        
        if not new_customer:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create customer"
            )
        
        return CustomerResponse(**new_customer)
    finally:
        close_db_connection(conn)


@app.get("/api/customers", response_model=List[CustomerResponse], tags=["Customers"])
def list_customers(
    active_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get all customers."""
    conn = get_db()
    try:
        customers = get_all_customers(conn, active_only)
        return [CustomerResponse(**customer) for customer in customers]
    finally:
        close_db_connection(conn)


@app.get("/api/customers/{customer_id}", response_model=CustomerResponse, tags=["Customers"])
def get_customer(
    customer_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific customer by ID."""
    conn = get_db()
    try:
        customer = get_customer_by_id(conn, customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        return CustomerResponse(**customer)
    finally:
        close_db_connection(conn)


@app.patch("/api/customers/{customer_id}", response_model=CustomerResponse, tags=["Customers"])
def update_customer_info(
    customer_id: int,
    customer_update: CustomerUpdate,
    current_user: dict = Depends(get_current_active_worker)
):
    """Update customer information."""
    conn = get_db()
    try:
        updated_customer = update_customer(
            conn,
            customer_id,
            customer_update.full_name,
            customer_update.phone,
            customer_update.email,
            customer_update.address,
            customer_update.is_active
        )
        
        if not updated_customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found or no changes made"
            )
        
        return CustomerResponse(**updated_customer)
    finally:
        close_db_connection(conn)


# ============================================================================
# VEHICLE ENDPOINTS
# ============================================================================

@app.post("/api/vehicles", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED, tags=["Vehicles"])
def create_new_vehicle(
    vehicle_data: VehicleCreate,
    current_user: dict = Depends(get_current_active_worker)
):
    """Register a new vehicle for a customer."""
    conn = get_db()
    try:
        new_vehicle = create_vehicle(
            conn,
            vehicle_data.customer_id,
            vehicle_data.make,
            vehicle_data.model,
            vehicle_data.year,
            vehicle_data.plate_number
        )
        
        if not new_vehicle:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create vehicle. Customer may not exist."
            )
        
        return VehicleResponse(**new_vehicle)
    finally:
        close_db_connection(conn)


@app.get("/api/vehicles", response_model=List[VehicleResponse], tags=["Vehicles"])
def list_vehicles(current_user: dict = Depends(get_current_user)):
    """Get all vehicles in the system."""
    conn = get_db()
    try:
        vehicles = get_all_vehicles(conn)
        return [VehicleResponse(**vehicle) for vehicle in vehicles]
    finally:
        close_db_connection(conn)


@app.get("/api/vehicles/{vehicle_id}", response_model=VehicleResponse, tags=["Vehicles"])
def get_vehicle(
    vehicle_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific vehicle by ID."""
    conn = get_db()
    try:
        vehicle = get_vehicle_by_id(conn, vehicle_id)
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )
        return VehicleResponse(**vehicle)
    finally:
        close_db_connection(conn)


@app.get("/api/customers/{customer_id}/vehicles", response_model=List[VehicleResponse], tags=["Vehicles"])
def get_customer_vehicles(
    customer_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get all vehicles owned by a specific customer."""
    conn = get_db()
    try:
        vehicles = get_vehicles_by_customer(conn, customer_id)
        return [VehicleResponse(**vehicle) for vehicle in vehicles]
    finally:
        close_db_connection(conn)


# ============================================================================
# JOB ENDPOINTS
# ============================================================================

@app.post("/api/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED, tags=["Jobs"])
def create_new_job(
    job_data: JobCreate,
    current_user: dict = Depends(get_current_active_worker)
):
    """Create a new job card for a vehicle."""
    conn = get_db()
    try:
        new_job = create_job(
            conn,
            job_data.vehicle_id,
            job_data.description,
            job_data.assigned_worker
        )
        
        if not new_job:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create job. Vehicle may not exist."
            )
        
        return JobResponse(**new_job)
    finally:
        close_db_connection(conn)


@app.get("/api/jobs", response_model=List[JobResponse], tags=["Jobs"])
def list_jobs(
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all jobs, optionally filtered by status."""
    conn = get_db()
    try:
        jobs = get_all_jobs(conn, status_filter)
        return [JobResponse(**job) for job in jobs]
    finally:
        close_db_connection(conn)


@app.get("/api/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
def get_job(
    job_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific job by ID."""
    conn = get_db()
    try:
        job = get_job_by_id(conn, job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        return JobResponse(**job)
    finally:
        close_db_connection(conn)


@app.get("/api/my-jobs", response_model=List[JobResponse], tags=["Jobs"])
def get_my_assigned_jobs(current_user: dict = Depends(get_current_active_worker)):
    """Get all jobs assigned to the current user."""
    conn = get_db()
    try:
        jobs = get_jobs_by_worker(conn, current_user["id"])
        return [JobResponse(**job) for job in jobs]
    finally:
        close_db_connection(conn)


@app.patch("/api/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
def update_job_info(
    job_id: int,
    job_update: JobUpdate,
    current_user: dict = Depends(get_current_active_worker)
):
    """Update job information."""
    conn = get_db()
    try:
        updated_job = update_job(
            conn,
            job_id,
            job_update.assigned_worker,
            job_update.description,
            job_update.status.value if job_update.status else None
        )
        
        if not updated_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found or no changes made"
            )
        
        return JobResponse(**updated_job)
    finally:
        close_db_connection(conn)


# ============================================================================
# JOB NOTES ENDPOINTS
# ============================================================================

@app.post("/api/job-notes", response_model=JobNoteResponse, status_code=status.HTTP_201_CREATED, tags=["Job Notes"])
def add_job_note(
    note_data: JobNoteCreate,
    current_user: dict = Depends(get_current_active_worker)
):
    """Add a note to a job."""
    conn = get_db()
    try:
        new_note = create_job_note(
            conn,
            note_data.job_id,
            current_user["id"],
            note_data.note
        )
        
        if not new_note:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create job note. Job may not exist."
            )
        
        return JobNoteResponse(**new_note)
    finally:
        close_db_connection(conn)


@app.get("/api/jobs/{job_id}/notes", response_model=List[JobNoteResponse], tags=["Job Notes"])
def get_job_notes(
    job_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get all notes for a specific job."""
    conn = get_db()
    try:
        notes = get_notes_by_job(conn, job_id)
        return [JobNoteResponse(**note) for note in notes]
    finally:
        close_db_connection(conn)


# ============================================================================
# INVOICE ENDPOINTS
# ============================================================================

@app.post("/api/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED, tags=["Invoices"])
def create_new_invoice(
    invoice_data: InvoiceCreate,
    current_user: dict = Depends(get_current_active_worker)
):
    """Create an invoice for a completed job."""
    conn = get_db()
    try:
        new_invoice = create_invoice(
            conn,
            invoice_data.job_id,
            invoice_data.total_amount
        )
        
        if not new_invoice:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create invoice. Job may not exist or already has an invoice."
            )
        
        return InvoiceResponse(**new_invoice)
    finally:
        close_db_connection(conn)


@app.get("/api/invoices", response_model=List[InvoiceResponse], tags=["Invoices"])
def list_invoices(
    unpaid_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get all invoices."""
    conn = get_db()
    try:
        invoices = get_all_invoices(conn, unpaid_only)
        return [InvoiceResponse(**invoice) for invoice in invoices]
    finally:
        close_db_connection(conn)


@app.get("/api/jobs/{job_id}/invoice", response_model=InvoiceResponse, tags=["Invoices"])
def get_job_invoice(
    job_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get invoice for a specific job."""
    conn = get_db()
    try:
        invoice = get_invoice_by_job(conn, job_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found for this job"
            )
        return InvoiceResponse(**invoice)
    finally:
        close_db_connection(conn)


@app.patch("/api/invoices/{invoice_id}", response_model=InvoiceResponse, tags=["Invoices"])
def update_invoice_info(
    invoice_id: int,
    invoice_update: InvoiceUpdate,
    current_user: dict = Depends(get_current_active_worker)
):
    """Update invoice information."""
    conn = get_db()
    try:
        updated_invoice = update_invoice(
            conn,
            invoice_id,
            invoice_update.total_amount,
            invoice_update.is_paid
        )
        
        if not updated_invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found or no changes made"
            )
        
        return InvoiceResponse(**updated_invoice)
    finally:
        close_db_connection(conn)


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/health", tags=["System"])
def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "message": "API is running"}


# ============================================================================
# RUN THE APPLICATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)