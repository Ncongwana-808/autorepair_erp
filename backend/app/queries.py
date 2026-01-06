"""
queries.py - Raw SQL queries for the Auto Repair Workshop ERP

This module contains all database operations using raw SQL with psycopg3.
Each function follows a simple pattern:
1. Get database connection
2. Execute SQL query
3. Fetch results (if needed)
4. Return data or None

KEY DIFFERENCE FROM PSYCOPG2:
- psycopg3 uses 'conn.execute()' directly (no need for cursor in simple cases)
- Use 'row_factory' for dict results instead of RealDictCursor
- Exceptions are in psycopg.errors instead of psycopg2
"""

from typing import Optional, List, Dict, Any
import psycopg
from psycopg.rows import dict_row


# ============================================================================
# USER QUERIES
# ============================================================================

def create_user(conn, username: str, password_hash: str, role: str) -> Optional[Dict[str, Any]]:
    """
    Create a new user in the database.
    
    HOW IT WORKS:
    1. Takes a database connection and user details
    2. Inserts new row into 'users' table
    3. RETURNING * gives us back the created user data
    4. dict_row returns data as a dictionary (easy to work with)
    
    Args:
        conn: Database connection object
        username: Unique username
        password_hash: Hashed password (NEVER store plain passwords!)
        role: 'admin' or 'worker'
    
    Returns:
        Dictionary with user data or None if failed
    """
    try:
        # psycopg3 uses 'with conn.cursor()' and row_factory
        with conn.cursor(row_factory=dict_row) as cursor:
            # SQL query with placeholders (%s) to prevent SQL injection
            query = """
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, %s)
                RETURNING id, username, role, is_active, created_at
            """
            # Execute with actual values - psycopg3 safely escapes them
            cursor.execute(query, (username, password_hash, role))
            conn.commit()  # Save changes to database
            return cursor.fetchone()  # Get the returned row as dict
    except psycopg.errors.UniqueViolation:
        # This happens if username already exists (UNIQUE constraint)
        conn.rollback()  # Undo the failed transaction
        return None
    except Exception as e:
        conn.rollback()
        print(f"Error creating user: {e}")
        return None


def get_user_by_username(conn, username: str) -> Optional[Dict[str, Any]]:
    """
    Find a user by their username.
    
    HOW IT WORKS:
    1. SELECT query to find matching username
    2. fetchone() returns single row (or None if not found)
    3. We include password_hash here for login verification
    
    Args:
        conn: Database connection
        username: Username to search for
    
    Returns:
        User dict including password_hash, or None
    """
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            query = """
                SELECT id, username, password_hash, role, is_active, created_at
                FROM users
                WHERE username = %s
            """
            cursor.execute(query, (username,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None


def get_user_by_id(conn, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Find a user by their ID.
    
    Similar to get_user_by_username but searches by ID instead.
    Used when we have user_id from JWT token.
    """
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            query = """
                SELECT id, username, role, is_active, created_at
                FROM users
                WHERE id = %s
            """
            cursor.execute(query, (user_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Error fetching user by ID: {e}")
        return None


def update_user(conn, user_id: int, role: Optional[str] = None, 
                is_active: Optional[bool] = None) -> Optional[Dict[str, Any]]:
    """
    Update user information.
    
    HOW IT WORKS:
    1. Build SQL dynamically based on what fields need updating
    2. Only update fields that are provided (not None)
    3. This prevents accidentally overwriting data
    
    Args:
        conn: Database connection
        user_id: ID of user to update
        role: New role (optional)
        is_active: New active status (optional)
    
    Returns:
        Updated user dict or None
    """
    try:
        # Build the SET clause dynamically
        updates = []
        params = []
        
        if role is not None:
            updates.append("role = %s")
            params.append(role)
        
        if is_active is not None:
            updates.append("is_active = %s")
            params.append(is_active)
        
        # If nothing to update, return None
        if not updates:
            return None
        
        # Add user_id at the end of params for WHERE clause
        params.append(user_id)
        
        with conn.cursor(row_factory=dict_row) as cursor:
            query = f"""
                UPDATE users
                SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, username, role, is_active, created_at
            """
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchone()
    except Exception as e:
        conn.rollback()
        print(f"Error updating user: {e}")
        return None


def get_all_users(conn) -> List[Dict[str, Any]]:
    """
    Get all users from database.
    
    HOW IT WORKS:
    1. SELECT all users
    2. fetchall() returns list of all rows
    3. Returns empty list if no users (not None)
    """
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            query = """
                SELECT id, username, role, is_active, created_at
                FROM users
                ORDER BY created_at DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching all users: {e}")
        return []


# ============================================================================
# CUSTOMER QUERIES
# ============================================================================

def create_customer(conn, full_name: str, phone: Optional[str] = None,
                   email: Optional[str] = None, address: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Create a new customer.
    
    HOW IT WORKS:
    1. Only full_name is required (NOT NULL in database)
    2. Other fields can be NULL (optional)
    3. RETURNING * gives us back all the created data including auto-generated ID
    """
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            query = """
                INSERT INTO customers (full_name, phone, email, address)
                VALUES (%s, %s, %s, %s)
                RETURNING id, full_name, phone, email, address, is_active, created_at
            """
            cursor.execute(query, (full_name, phone, email, address))
            conn.commit()
            return cursor.fetchone()
    except Exception as e:
        conn.rollback()
        print(f"Error creating customer: {e}")
        return None


def get_customer_by_id(conn, customer_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a single customer by ID.
    """
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            query = """
                SELECT id, full_name, phone, email, address, is_active, created_at
                FROM customers
                WHERE id = %s
            """
            cursor.execute(query, (customer_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Error fetching customer: {e}")
        return None


def get_all_customers(conn, active_only: bool = False) -> List[Dict[str, Any]]:
    """
    Get all customers.
    
    HOW IT WORKS:
    1. Can filter by is_active flag (soft delete pattern)
    2. If active_only=True, only returns active customers
    3. This way we never lose data, just hide inactive ones
    """
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            if active_only:
                query = """
                    SELECT id, full_name, phone, email, address, is_active, created_at
                    FROM customers
                    WHERE is_active = TRUE
                    ORDER BY full_name
                """
            else:
                query = """
                    SELECT id, full_name, phone, email, address, is_active, created_at
                    FROM customers
                    ORDER BY full_name
                """
            cursor.execute(query)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching customers: {e}")
        return []


def update_customer(conn, customer_id: int, full_name: Optional[str] = None,
                   phone: Optional[str] = None, email: Optional[str] = None,
                   address: Optional[str] = None, is_active: Optional[bool] = None) -> Optional[Dict[str, Any]]:
    """
    Update customer information.
    
    Same dynamic update pattern as update_user.
    """
    try:
        updates = []
        params = []
        
        if full_name is not None:
            updates.append("full_name = %s")
            params.append(full_name)
        
        if phone is not None:
            updates.append("phone = %s")
            params.append(phone)
        
        if email is not None:
            updates.append("email = %s")
            params.append(email)
        
        if address is not None:
            updates.append("address = %s")
            params.append(address)
        
        if is_active is not None:
            updates.append("is_active = %s")
            params.append(is_active)
        
        if not updates:
            return None
        
        params.append(customer_id)
        
        with conn.cursor(row_factory=dict_row) as cursor:
            query = f"""
                UPDATE customers
                SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, full_name, phone, email, address, is_active, created_at
            """
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchone()
    except Exception as e:
        conn.rollback()
        print(f"Error updating customer: {e}")
        return None


# ============================================================================
# VEHICLE QUERIES
# ============================================================================

def create_vehicle(conn, customer_id: int, make: str, model: str,
                  year: int, plate_number: str) -> Optional[Dict[str, Any]]:
    """
    Register a new vehicle for a customer.
    
    HOW IT WORKS:
    1. customer_id is a foreign key - must reference existing customer
    2. If customer doesn't exist, PostgreSQL will raise an error
    3. This enforces referential integrity
    """
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            query = """
                INSERT INTO vehicles (customer_id, make, model, year, plate_number)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, customer_id, make, model, year, plate_number, created_at
            """
            cursor.execute(query, (customer_id, make, model, year, plate_number))
            conn.commit()
            return cursor.fetchone()
    except psycopg.errors.ForeignKeyViolation as e:
        conn.rollback()
        print(f"Foreign key error: {e}")
        return None
    except Exception as e:
        conn.rollback()
        print(f"Error creating vehicle: {e}")
        return None


def get_vehicle_by_id(conn, vehicle_id: int) -> Optional[Dict[str, Any]]:
    """Get a single vehicle by ID."""
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            query = """
                SELECT id, customer_id, make, model, year, plate_number, created_at
                FROM vehicles
                WHERE id = %s
            """
            cursor.execute(query, (vehicle_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Error fetching vehicle: {e}")
        return None


def get_vehicles_by_customer(conn, customer_id: int) -> List[Dict[str, Any]]:
    """
    Get all vehicles owned by a specific customer.
    
    HOW IT WORKS:
    1. Filter by customer_id foreign key
    2. Shows relationship: one customer can have many vehicles
    """
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            query = """
                SELECT id, customer_id, make, model, year, plate_number, created_at
                FROM vehicles
                WHERE customer_id = %s
                ORDER BY created_at DESC
            """
            cursor.execute(query, (customer_id,))
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching customer vehicles: {e}")
        return []


def get_all_vehicles(conn) -> List[Dict[str, Any]]:
    """Get all vehicles in the system."""
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            query = """
                SELECT id, customer_id, make, model, year, plate_number, created_at
                FROM vehicles
                ORDER BY created_at DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching all vehicles: {e}")
        return []


# ============================================================================
# JOB QUERIES
# ============================================================================

def create_job(conn, vehicle_id: int, description: str,
               assigned_worker: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Create a new job card.
    
    HOW IT WORKS:
    1. Job starts with status 'created' (default in database)
    2. Can optionally assign a worker immediately
    3. Links to a vehicle (which links to a customer)
    """
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            query = """
                INSERT INTO jobs (vehicle_id, description, assigned_worker)
                VALUES (%s, %s, %s)
                RETURNING id, vehicle_id, assigned_worker, description, status, created_at, updated_at
            """
            cursor.execute(query, (vehicle_id, description, assigned_worker))
            conn.commit()
            return cursor.fetchone()
    except Exception as e:
        conn.rollback()
        print(f"Error creating job: {e}")
        return None


def get_job_by_id(conn, job_id: int) -> Optional[Dict[str, Any]]:
    """Get a single job by ID."""
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            query = """
                SELECT id, vehicle_id, assigned_worker, description, status, created_at, updated_at
                FROM jobs
                WHERE id = %s
            """
            cursor.execute(query, (job_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Error fetching job: {e}")
        return None


def get_jobs_by_worker(conn, worker_id: int) -> List[Dict[str, Any]]:
    """
    Get all jobs assigned to a specific worker.
    
    Use case: Worker logs in and sees their assigned tasks.
    """
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            query = """
                SELECT id, vehicle_id, assigned_worker, description, status, created_at, updated_at
                FROM jobs
                WHERE assigned_worker = %s
                ORDER BY created_at DESC
            """
            cursor.execute(query, (worker_id,))
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching worker jobs: {e}")
        return []


def get_all_jobs(conn, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all jobs, optionally filtered by status.
    
    HOW IT WORKS:
    1. If status provided, filter by it
    2. Useful for dashboards: "show me all in_progress jobs"
    """
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            if status:
                query = """
                    SELECT id, vehicle_id, assigned_worker, description, status, created_at, updated_at
                    FROM jobs
                    WHERE status = %s
                    ORDER BY created_at DESC
                """
                cursor.execute(query, (status,))
            else:
                query = """
                    SELECT id, vehicle_id, assigned_worker, description, status, created_at, updated_at
                    FROM jobs
                    ORDER BY created_at DESC
                """
                cursor.execute(query)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching jobs: {e}")
        return []


def update_job(conn, job_id: int, assigned_worker: Optional[int] = None,
               description: Optional[str] = None, status: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Update job information.
    
    HOW IT WORKS:
    1. Can update worker assignment, description, or status
    2. updated_at is automatically updated by database trigger!
    """
    try:
        updates = []
        params = []
        
        if assigned_worker is not None:
            updates.append("assigned_worker = %s")
            params.append(assigned_worker)
        
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        
        if status is not None:
            updates.append("status = %s")
            params.append(status)
        
        if not updates:
            return None
        
        params.append(job_id)
        
        with conn.cursor(row_factory=dict_row) as cursor:
            query = f"""
                UPDATE jobs
                SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, vehicle_id, assigned_worker, description, status, created_at, updated_at
            """
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchone()
    except Exception as e:
        conn.rollback()
        print(f"Error updating job: {e}")
        return None


# ============================================================================
# JOB NOTE QUERIES
# ============================================================================

def create_job_note(conn, job_id: int, worker_id: int, note: str) -> Optional[Dict[str, Any]]:
    """
    Add a note to a job.
    
    HOW IT WORKS:
    1. Workers document their progress, findings, or issues
    2. Creates chronological log of work done
    3. Like a diary for each job
    """
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            query = """
                INSERT INTO job_notes (job_id, worker_id, note)
                VALUES (%s, %s, %s)
                RETURNING id, job_id, worker_id, note, created_at
            """
            cursor.execute(query, (job_id, worker_id, note))
            conn.commit()
            return cursor.fetchone()
    except Exception as e:
        conn.rollback()
        print(f"Error creating job note: {e}")
        return None


def get_notes_by_job(conn, job_id: int) -> List[Dict[str, Any]]:
    """
    Get all notes for a specific job.
    
    Returns notes in chronological order (oldest first).
    """
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            query = """
                SELECT id, job_id, worker_id, note, created_at
                FROM job_notes
                WHERE job_id = %s
                ORDER BY created_at ASC
            """
            cursor.execute(query, (job_id,))
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching job notes: {e}")
        return []


# ============================================================================
# INVOICE QUERIES
# ============================================================================

def create_invoice(conn, job_id: int, total_amount: float) -> Optional[Dict[str, Any]]:
    """
    Create an invoice for a completed job.
    
    HOW IT WORKS:
    1. job_id is UNIQUE - one invoice per job
    2. Starts with is_paid = FALSE
    3. Business rule: job should be completed before invoicing
    """
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            query = """
                INSERT INTO invoices (job_id, total_amount)
                VALUES (%s, %s)
                RETURNING id, job_id, total_amount, is_paid, created_at
            """
            cursor.execute(query, (job_id, total_amount))
            conn.commit()
            return cursor.fetchone()
    except psycopg.errors.UniqueViolation:
        # Invoice already exists for this job
        conn.rollback()
        return None
    except Exception as e:
        conn.rollback()
        print(f"Error creating invoice: {e}")
        return None


def get_invoice_by_job(conn, job_id: int) -> Optional[Dict[str, Any]]:
    """Get invoice for a specific job."""
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            query = """
                SELECT id, job_id, total_amount, is_paid, created_at
                FROM invoices
                WHERE job_id = %s
            """
            cursor.execute(query, (job_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Error fetching invoice: {e}")
        return None


def update_invoice(conn, invoice_id: int, total_amount: Optional[float] = None,
                  is_paid: Optional[bool] = None) -> Optional[Dict[str, Any]]:
    """
    Update invoice.
    
    Common use case: Mark invoice as paid (is_paid = TRUE).
    """
    try:
        updates = []
        params = []
        
        if total_amount is not None:
            updates.append("total_amount = %s")
            params.append(total_amount)
        
        if is_paid is not None:
            updates.append("is_paid = %s")
            params.append(is_paid)
        
        if not updates:
            return None
        
        params.append(invoice_id)
        
        with conn.cursor(row_factory=dict_row) as cursor:
            query = f"""
                UPDATE invoices
                SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, job_id, total_amount, is_paid, created_at
            """
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchone()
    except Exception as e:
        conn.rollback()
        print(f"Error updating invoice: {e}")
        return None


def get_all_invoices(conn, unpaid_only: bool = False) -> List[Dict[str, Any]]:
    """
    Get all invoices.
    
    Can filter to show only unpaid invoices (for tracking receivables).
    """
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            if unpaid_only:
                query = """
                    SELECT id, job_id, total_amount, is_paid, created_at
                    FROM invoices
                    WHERE is_paid = FALSE
                    ORDER BY created_at DESC
                """
            else:
                query = """
                    SELECT id, job_id, total_amount, is_paid, created_at
                    FROM invoices
                    ORDER BY created_at DESC
                """
            cursor.execute(query)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching invoices: {e}")
        return []