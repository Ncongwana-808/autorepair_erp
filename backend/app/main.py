"""
main.py - FastAPI Application Entry Point

This is the heart of your API where all routes are defined.

STRUCTURE:
1. Authentication routes (register, login)
2. User management routes (admin only)
3. Customer routes
4. Vehicle routes
5. Job routes
6. Job notes routes
7. Invoice routes
"""

from fastapi import FastAPI, Depends, HTTPException, status
from typing import List, Optional

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
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Auto Repair Workshop ERP",
    description="Backend API for managing auto repair workshop operations",
    version="1.0.0"
)


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["Root"])
def read_root():
    """
    Welcome endpoint - Shows API is running.
    
    This is your landing page when someone visits the API.
    """
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
    
    SECURITY NOTE:
    - In production, you might want to restrict who can create admin accounts
    - For now, anyone can register as admin or worker
    
    Example request body:
    {
        "username": "john_worker",
        "password": "securePassword123",
        "role": "worker"
    }
    
    Returns:
    {
        "access_token": "eyJhbGci...",
        "token_type": "bearer",
        "user": {
            "id": 1,
            "username": "john_worker",
            "role": "worker"
        }
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
    
    HOW IT WORKS:
    1. User sends username and password
    2. We verify credentials against database
    3. If valid, create and return JWT token
    4. If invalid, return 401 error
    
    THE TOKEN CONTAINS:
    - user_id
    - username
    - role (admin or worker)
    - expiration time
    
    Example request:
    {
        "username": "john_worker",
        "password": "securePassword123"
    }
    
    Returns JWT token that client must include in future requests:
    Authorization: Bearer <token>
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
    """
    Get current authenticated user's information.
    
    HOW IT WORKS:
    1. Extract token from Authorization header
    2. Validate token and get user
    3. Return user information
    
    USE THIS TO:
    - Check if user is still logged in
    - Get user details for UI
    - Verify token is valid
    
    REQUIRES:
    - Authorization: Bearer <token> header
    """
    return UserResponse(**current_user)


# ============================================================================
# USER MANAGEMENT ENDPOINTS (ADMIN ONLY)
# ============================================================================

@app.get("/users", response_model=List[UserResponse], tags=["Users"])
def list_all_users(admin: dict = Depends(get_current_active_admin)):
    """
    Get all users in the system.
    
    ADMIN ONLY - Protected by get_current_active_admin dependency.
    
    Returns list of all users (workers and admins).
    """
    conn = get_db()
    try:
        users = get_all_users(conn)
        return [UserResponse(**user) for user in users]
    finally:
        close_db_connection(conn)


@app.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
def get_user(user_id: int, admin: dict = Depends(get_current_active_admin)):
    """
    Get a specific user by ID.
    
    ADMIN ONLY endpoint.
    """
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


@app.patch("/users/{user_id}", response_model=UserResponse, tags=["Users"])
def update_user_info(
    user_id: int,
    user_update: UserUpdate,
    admin: dict = Depends(get_current_active_admin)
):
    """
    Update user information (role or active status).
    
    ADMIN ONLY - Can change:
    - User role (admin <-> worker)
    - Active status (enable/disable account)
    
    Example:
    PATCH /users/5
    {
        "is_active": false  // Disable user account
    }
    """
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

@app.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED, tags=["Customers"])
def create_new_customer(
    customer_data: CustomerCreate,
    current_user: dict = Depends(get_current_active_worker)
):
    """
    Create a new customer.
    
    WORKERS AND ADMINS can create customers.
    
    Example:
    POST /customers
    {
        "full_name": "John Doe",
        "phone": "555-1234",
        "email": "john@example.com",
        "address": "123 Main St"
    }
    """
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


@app.get("/customers", response_model=List[CustomerResponse], tags=["Customers"])
def list_customers(
    active_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all customers.
    
    Query parameters:
    - active_only: If true, only return active customers
    
    Example:
    GET /customers?active_only=true
    """
    conn = get_db()
    try:
        customers = get_all_customers(conn, active_only)
        return [CustomerResponse(**customer) for customer in customers]
    finally:
        close_db_connection(conn)


@app.get("/customers/{customer_id}", response_model=CustomerResponse, tags=["Customers"])
def get_customer(
    customer_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific customer by ID.
    """
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


@app.patch("/customers/{customer_id}", response_model=CustomerResponse, tags=["Customers"])
def update_customer_info(
    customer_id: int,
    customer_update: CustomerUpdate,
    current_user: dict = Depends(get_current_active_worker)
):
    """
    Update customer information.
    
    Can update: name, phone, email, address, or active status.
    """
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

@app.post("/vehicles", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED, tags=["Vehicles"])
def create_new_vehicle(
    vehicle_data: VehicleCreate,
    current_user: dict = Depends(get_current_active_worker)
):
    """
    Register a new vehicle for a customer.
    
    Example:
    POST /vehicles
    {
        "customer_id": 1,
        "make": "Toyota",
        "model": "Camry",
        "year": 2020,
        "plate_number": "ABC-1234"
    }
    """
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


@app.get("/vehicles", response_model=List[VehicleResponse], tags=["Vehicles"])
def list_vehicles(current_user: dict = Depends(get_current_user)):
    """
    Get all vehicles in the system.
    """
    conn = get_db()
    try:
        vehicles = get_all_vehicles(conn)
        return [VehicleResponse(**vehicle) for vehicle in vehicles]
    finally:
        close_db_connection(conn)


@app.get("/vehicles/{vehicle_id}", response_model=VehicleResponse, tags=["Vehicles"])
def get_vehicle(
    vehicle_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific vehicle by ID.
    """
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


@app.get("/customers/{customer_id}/vehicles", response_model=List[VehicleResponse], tags=["Vehicles"])
def get_customer_vehicles(
    customer_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all vehicles owned by a specific customer.
    
    Example: GET /customers/1/vehicles
    Returns all vehicles for customer with ID 1.
    """
    conn = get_db()
    try:
        vehicles = get_vehicles_by_customer(conn, customer_id)
        return [VehicleResponse(**vehicle) for vehicle in vehicles]
    finally:
        close_db_connection(conn)


# ============================================================================
# JOB ENDPOINTS
# ============================================================================

@app.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED, tags=["Jobs"])
def create_new_job(
    job_data: JobCreate,
    current_user: dict = Depends(get_current_active_worker)
):
    """
    Create a new job card for a vehicle.
    
    Example:
    POST /jobs
    {
        "vehicle_id": 1,
        "description": "Oil change and tire rotation",
        "assigned_worker": 3  // Optional
    }
    """
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


@app.get("/jobs", response_model=List[JobResponse], tags=["Jobs"])
def list_jobs(
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all jobs, optionally filtered by status.
    
    Query parameters:
    - status: Filter by job status (created, in_progress, completed, etc.)
    
    Example:
    GET /jobs?status=in_progress
    """
    conn = get_db()
    try:
        jobs = get_all_jobs(conn, status_filter)
        return [JobResponse(**job) for job in jobs]
    finally:
        close_db_connection(conn)


@app.get("/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
def get_job(
    job_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific job by ID.
    """
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


@app.get("/my-jobs", response_model=List[JobResponse], tags=["Jobs"])
def get_my_assigned_jobs(current_user: dict = Depends(get_current_active_worker)):
    """
    Get all jobs assigned to the current user.
    
    Workers see their own assigned jobs.
    Admins see all jobs assigned to them (if any).
    """
    conn = get_db()
    try:
        jobs = get_jobs_by_worker(conn, current_user["id"])
        return [JobResponse(**job) for job in jobs]
    finally:
        close_db_connection(conn)


@app.patch("/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
def update_job_info(
    job_id: int,
    job_update: JobUpdate,
    current_user: dict = Depends(get_current_active_worker)
):
    """
    Update job information.
    
    Can update:
    - assigned_worker: Change who's working on it
    - description: Update job details
    - status: Move through workflow (created -> in_progress -> completed)
    
    Example:
    PATCH /jobs/5
    {
        "status": "in_progress"
    }
    """
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

@app.post("/job-notes", response_model=JobNoteResponse, status_code=status.HTTP_201_CREATED, tags=["Job Notes"])
def add_job_note(
    note_data: JobNoteCreate,
    current_user: dict = Depends(get_current_active_worker)
):
    """
    Add a note to a job.
    
    Workers document their progress, findings, or issues.
    
    Example:
    POST /job-notes
    {
        "job_id": 5,
        "note": "Replaced oil filter. Found brake pads worn, recommend replacement."
    }
    """
    conn = get_db()
    try:
        new_note = create_job_note(
            conn,
            note_data.job_id,
            current_user["id"],  # Automatically use current user as worker
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


@app.get("/jobs/{job_id}/notes", response_model=List[JobNoteResponse], tags=["Job Notes"])
def get_job_notes(
    job_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all notes for a specific job.
    
    Returns chronological log of work done.
    """
    conn = get_db()
    try:
        notes = get_notes_by_job(conn, job_id)
        return [JobNoteResponse(**note) for note in notes]
    finally:
        close_db_connection(conn)


# ============================================================================
# INVOICE ENDPOINTS
# ============================================================================

@app.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED, tags=["Invoices"])
def create_new_invoice(
    invoice_data: InvoiceCreate,
    current_user: dict = Depends(get_current_active_worker)
):
    """
    Create an invoice for a completed job.
    
    Example:
    POST /invoices
    {
        "job_id": 5,
        "total_amount": 250.50
    }
    """
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


@app.get("/invoices", response_model=List[InvoiceResponse], tags=["Invoices"])
def list_invoices(
    unpaid_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all invoices.
    
    Query parameters:
    - unpaid_only: If true, only return unpaid invoices
    
    Example:
    GET /invoices?unpaid_only=true
    """
    conn = get_db()
    try:
        invoices = get_all_invoices(conn, unpaid_only)
        return [InvoiceResponse(**invoice) for invoice in invoices]
    finally:
        close_db_connection(conn)


@app.get("/jobs/{job_id}/invoice", response_model=InvoiceResponse, tags=["Invoices"])
def get_job_invoice(
    job_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get invoice for a specific job.
    """
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


@app.patch("/invoices/{invoice_id}", response_model=InvoiceResponse, tags=["Invoices"])
def update_invoice_info(
    invoice_id: int,
    invoice_update: InvoiceUpdate,
    current_user: dict = Depends(get_current_active_worker)
):
    """
    Update invoice information.
    
    Common use: Mark invoice as paid.
    
    Example:
    PATCH /invoices/3
    {
        "is_paid": true
    }
    """
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
    """
    Simple health check endpoint.
    
    Returns 200 OK if API is running.
    Use this for monitoring and deployment health checks.
    """
    return {"status": "healthy", "message": "API is running"}


# ============================================================================
# RUN THE APPLICATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)