from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
import jwt
import os

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Configuration
SECRET_KEY = "your-very-secret-key-change-this-for-production" # In a real app, use environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ──────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────

class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_email: str
    user_name: str

# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserSignup, request: Request):
    db = request.app.mongodb
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    user_dict = {
        "email": user.email,
        "password": get_password_hash(user.password),
        "full_name": user.full_name,
        "created_at": datetime.utcnow()
    }
    
    await db.users.insert_one(user_dict)
    
    # Generate token
    token = create_access_token({"sub": user.email})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_email": user.email,
        "user_name": user.full_name
    }

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, request: Request):
    db = request.app.mongodb
    
    # Find user
    user = await db.users.find_one({"email": user_credentials.email})
    if not user or not verify_password(user_credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate token
    token = create_access_token({"sub": user["email"]})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_email": user["email"],
        "user_name": user["full_name"]
    }

@router.get("/me")
async def get_current_user(request: Request):
    # This is a placeholder. In a full app, you'd extract the JWT from the header
    # and look up the user in the database.
    return {"message": "Authenticated user endpoint placeholder"}
