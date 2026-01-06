"""
auth.py - Authentication and Authorization Module

This module handles:
1. Password hashing and verification
2. JWT token creation and validation
3. User authentication (login)
4. Role-based access control (admin vs worker)

KEY CONCEPTS:
- Never store plain passwords (use bcrypt hashing)
- JWT tokens carry user identity and role
- Tokens expire after set time for security
- Dependencies verify tokens on protected routes
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv

from models import TokenData, UserRole
from database import get_db, close_db_connection
from queries import get_user_by_username, get_user_by_id

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme for FastAPI
security = HTTPBearer()


# ============================================================================
# PASSWORD FUNCTIONS
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    HOW IT WORKS:
    1. Takes plain password like "myPassword123"
    2. Bcrypt adds random "salt" and hashes it
    3. Returns something like: "$2b$12$KIXxJ..."
    4. Same password = different hash each time (because of salt)
    5. This is ONE-WAY - cannot reverse to get original password
    
    Example:
        hashed = hash_password("worker123")
        # Returns: "$2b$12$abcd1234..."
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify if a plain password matches the hashed version.
    
    HOW IT WORKS:
    1. User logs in with "worker123"
    2. We get stored hash from database
    3. Bcrypt checks if plain password matches hash
    4. Returns True if match, False otherwise
    
    Example:
        is_valid = verify_password("worker123", stored_hash)
        # Returns: True or False
    
    Args:
        plain_password: Password user entered
        hashed_password: Hash stored in database
    
    Returns:
        True if password is correct, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# JWT TOKEN FUNCTIONS
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    HOW JWT WORKS:
    1. Take user data (id, username, role)
    2. Add expiration time
    3. Encode it with SECRET_KEY
    4. Return a token string like: "eyJhbGciOiJIUzI1NiIsInR5..."
    
    JWT Structure (3 parts separated by dots):
    - Header: Algorithm info
    - Payload: User data (NOT encrypted, just encoded!)
    - Signature: Proves token wasn't tampered with
    
    SECURITY NOTE:
    - Anyone can READ the payload (it's just base64)
    - But they CAN'T modify it without SECRET_KEY
    - That's why we don't put sensitive info in tokens
    
    Example:
        token = create_access_token(
            data={"user_id": 5, "username": "john", "role": "worker"}
        )
        # Returns JWT token string
    
    Args:
        data: Dictionary with user info
        expires_delta: How long token is valid (default: 24 hours)
    
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Create the JWT token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode and verify a JWT token.
    
    HOW IT WORKS:
    1. Take token from request header
    2. Verify signature using SECRET_KEY
    3. Check if token expired
    4. Extract user data from payload
    5. Return TokenData object or None if invalid
    
    WHAT CAN GO WRONG:
    - Token expired → JWTError
    - Token tampered with → Signature verification fails
    - Invalid format → JWTError
    
    Example:
        token_data = decode_access_token("eyJhbGciOiJI...")
        # Returns: TokenData(user_id=5, username="john", role="worker")
        # or None if invalid
    
    Args:
        token: JWT token string
    
    Returns:
        TokenData object or None if invalid
    """
    try:
        # Decode and verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extract user info from payload
        user_id: int = payload.get("user_id")
        username: str = payload.get("username")
        role: str = payload.get("role")
        
        # Validate data exists
        if user_id is None or username is None or role is None:
            return None
        
        # Return structured data
        return TokenData(user_id=user_id, username=username, role=UserRole(role))
    
    except JWTError:
        return None


# ============================================================================
# AUTHENTICATION FUNCTION
# ============================================================================

def authenticate_user(username: str, password: str):
    """
    Authenticate a user with username and password.
    
    THE LOGIN FLOW:
    1. User sends username + password
    2. Look up user in database
    3. Check if user exists
    4. Check if user is active
    5. Verify password against stored hash
    6. Return user data if everything checks out
    
    Example:
        conn = get_db()
        user = authenticate_user("john", "worker123")
        conn.close()
        
        if user:
            # Login successful - create token
        else:
            # Login failed - wrong credentials
    
    Args:
        username: Username to authenticate
        password: Plain text password
    
    Returns:
        User dict if authenticated, None otherwise
    """
    conn = get_db()
    
    try:
        # Get user from database
        user = get_user_by_username(conn, username)
        
        # Check if user exists
        if not user:
            return None
        
        # Check if user is active
        if not user.get("is_active", False):
            return None
        
        # Verify password
        if not verify_password(password, user["password_hash"]):
            return None
        
        # Authentication successful!
        return user
    
    finally:
        close_db_connection(conn)


# ============================================================================
# FASTAPI DEPENDENCIES - ROUTE PROTECTION
# ============================================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    FastAPI dependency to get current authenticated user.
    
    HOW IT WORKS IN ROUTES:
    1. FastAPI extracts token from Authorization header
    2. This function validates the token
    3. Returns user data if valid
    4. Raises 401 error if invalid
    
    Example usage in route:
        @app.get("/profile")
        def get_profile(current_user = Depends(get_current_user)):
            return {"user": current_user}
    
    AUTHORIZATION HEADER FORMAT:
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5...
    
    Args:
        credentials: Automatically extracted by FastAPI
    
    Returns:
        User dictionary with id, username, role
    
    Raises:
        HTTPException: 401 if token invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Extract token from credentials
    token = credentials.credentials
    
    # Decode token
    token_data = decode_access_token(token)
    if token_data is None:
        raise credentials_exception
    
    # Get user from database to ensure they still exist and are active
    conn = get_db()
    try:
        user = get_user_by_id(conn, token_data.user_id)
        if user is None or not user.get("is_active", False):
            raise credentials_exception
        
        return user
    finally:
        close_db_connection(conn)


async def get_current_active_admin(current_user: dict = Depends(get_current_user)):
    """
    FastAPI dependency to require ADMIN role.
    
    HOW IT WORKS:
    1. First runs get_current_user (validates token)
    2. Then checks if user role is 'admin'
    3. Raises 403 error if not admin
    
    Example usage:
        @app.delete("/users/{user_id}")
        def delete_user(
            user_id: int, 
            admin = Depends(get_current_active_admin)
        ):
            # Only admins can reach this code
            return {"message": "User deleted"}
    
    USE THIS FOR:
    - User management endpoints
    - System configuration
    - Viewing all data
    - Critical operations
    
    Args:
        current_user: Automatically passed from get_current_user
    
    Returns:
        Admin user dictionary
    
    Raises:
        HTTPException: 403 if user is not an admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_current_active_worker(current_user: dict = Depends(get_current_user)):
    """
    FastAPI dependency to require WORKER role (or admin).
    
    HOW IT WORKS:
    1. Validates token
    2. Checks if user is worker or admin
    3. Admins can access worker endpoints too
    
    Example usage:
        @app.post("/customers")
        def create_customer(
            customer_data: CustomerCreate,
            worker = Depends(get_current_active_worker)
        ):
            # Workers and admins can create customers
            return {"message": "Customer created"}
    
    Args:
        current_user: Automatically passed from get_current_user
    
    Returns:
        Worker or admin user dictionary
    
    Raises:
        HTTPException: 403 if user is neither worker nor admin
    """
    role = current_user.get("role")
    if role not in ["worker", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Worker or Admin access required"
        )
    return current_user


# ============================================================================
# HELPER FUNCTION FOR ROUTE RESPONSES
# ============================================================================

def create_token_response(user: dict) -> dict:
    """
    Helper function to create a standardized token response.
    
    Called after successful login or registration.
    
    Args:
        user: User dictionary from database
    
    Returns:
        Dictionary with access_token and user info
    """
    access_token = create_access_token(
        data={
            "user_id": user["id"],
            "username": user["username"],
            "role": user["role"]
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"]
        }
    }


# ============================================================================
# IMPORTANT NOTES FOR YOUR .ENV FILE
# ============================================================================

"""
Make sure your .env file has:

SECRET_KEY=your-super-secret-key-at-least-32-characters-long
DB_HOST=localhost
DB_PORT=5432
DB_NAME=autorepair_db
DB_USER=postgres
DB_PASSWORD=your_password

To generate a secure SECRET_KEY, run in Python:
    import secrets
    print(secrets.token_urlsafe(32))
"""