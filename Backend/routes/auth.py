from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
from typing import Optional
import jwt
import os
import bcrypt

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Configuration
SECRET_KEY = "your-very-secret-key-change-this-for-production" # In a real app, use environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

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

def get_password_hash(password: str):
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict):
    from datetime import timezone
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create new user
    try:
        hashed_pwd = get_password_hash(user.password)
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Hashing failed: {str(e)}")
    
    user_dict = {
        "email": user.email,
        "password": hashed_pwd,
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
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    if not verify_password(user_credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate token
    token = create_access_token({"sub": user["email"]})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_email": user["email"],
        "user_name": user["full_name"]
    }
