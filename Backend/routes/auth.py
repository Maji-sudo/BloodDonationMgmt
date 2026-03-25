from fastapi import APIRouter, HTTPException, status, Request, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
from typing import Optional
import jwt
import os
import bcrypt
from services.mail_service import send_otp_mail
from pydantic import EmailStr

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

# ──────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────

class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    otp: str = Field(..., min_length=6, max_length=6)

class PasswordReset(BaseModel):
    email: EmailStr
    token: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class TokenVerification(BaseModel):
    email: EmailStr
    token: str = Field(..., min_length=6, max_length=6)

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

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(data: dict):
    from datetime import timezone
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    db = request.app.mongodb
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub") or payload.get("email")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = await db.users.find_one({"email": email.lower()})
    if user is None:
        raise credentials_exception
    return user

# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@router.post("/request-signup-otp")
async def request_signup_otp(data: ForgotPasswordRequest, request: Request, background_tasks: BackgroundTasks):
    import random
    db = request.app.mongodb
    normalized_email = data.email.lower()
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": normalized_email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Account already exists. Please log in.")
        
    # Generate OTP
    otp = str(random.randint(100000, 999999))
    expire_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Store in a temporary collection
    await db.pending_verifications.update_one(
        {"email": normalized_email},
        {"$set": {"otp": otp, "expires_at": expire_at}},
        upsert=True
    )
    
    # Send Email in background
    background_tasks.add_task(send_otp_mail, normalized_email, otp)
    
    return {"message": "OTP sent! Please check your email."}

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserSignup, request: Request, background_tasks: BackgroundTasks):
    import random
    db = request.app.mongodb
    # Normalize email
    normalized_email = user.email.lower()

    # Check passwords match
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # Check if user already exists
    existing_user = await db.users.find_one({"email": normalized_email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # 1. VERIFY OTP BEFORE CREATING
    pending = await db.pending_verifications.find_one({
        "email": normalized_email,
        "otp": user.otp
    })
    
    if not pending:
        raise HTTPException(status_code=400, detail="Invalid verification code.")
        
    if pending.get("expires_at") < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification code has expired.")

    # Create User (Starts as VERIFIED because OTP matched)
    hashed_password = get_password_hash(user.password)
    user_dict = {
        "email": normalized_email,
        "password": hashed_password,
        "full_name": user.full_name,
        "is_verified": True,
        "role": None,
        "created_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_dict)
    
    # Clean up pending verification
    await db.pending_verifications.delete_one({"email": normalized_email})
    
    return {
        "message": "User registered and verified successfully!",
        "user_email": normalized_email
    }

@router.post("/verify-signup")
async def verify_signup(data: TokenVerification, request: Request):
    db = request.app.mongodb
    normalized_email = data.email.lower()
    
    user = await db.users.find_one({
        "email": normalized_email,
        "verification_token": data.token
    })
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification code.")
        
    if user.get("verification_token_expires") < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification code has expired.")
        
    # Mark as verified
    await db.users.update_one(
        {"email": normalized_email},
        {
            "$set": {"is_verified": True},
            "$unset": {"verification_token": "", "verification_token_expires": ""}
        }
    )
    
    return {"message": "Email verified successfully! You can now log in."}

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, request: Request):
    db = request.app.mongodb
    normalized_email = user_credentials.email.lower()
    
    # Find user
    user = await db.users.find_one({"email": normalized_email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    if not verify_password(user_credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if verified
    if not user.get("is_verified", False):
        raise HTTPException(status_code=403, detail="Please verify your email before logging in.")
    
    # Generate token
    token = create_access_token({"sub": user["email"]})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_email": user["email"],
        "user_name": user["full_name"]
    }

@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, request: Request, background_tasks: BackgroundTasks):
    import random
    db = request.app.mongodb
    normalized_email = data.email.lower()
    
    # Check if user exists
    user = await db.users.find_one({"email": normalized_email})
    if not user:
        count = await db.users.count_documents({})
        print(f"DEBUG: Email {normalized_email} NOT FOUND in users collection (Total users: {count})")
        raise HTTPException(status_code=404, detail=f"User {normalized_email} not found in database.")
    
    print(f"DEBUG: Found user: {user.get('full_name')}. Proceeding to OTP...")
    
    # Generate 6-digit token
    token = str(random.randint(100000, 999999))
    expire_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Save token to user
    await db.users.update_one(
        {"email": normalized_email},
        {"$set": {
            "reset_token": token,
            "reset_token_expires": expire_at
        }}
    )
    
    # SEND EMAIL VIA SERVICE IN BACKGROUND
    try:
        background_tasks.add_task(send_otp_mail, normalized_email, token)
    except Exception as e:
        print(f"❌ MAIL ERROR LOGGING TASK: {str(e)}")
        print(f"RECOVERY TOKEN FOR {normalized_email}: {token}")
        raise HTTPException(status_code=500, detail="Failed to initiate verification email.")
    
    return {"message": "Verification code sent to your email. Please check your inbox."}


@router.post("/verify-token")
async def verify_token(data: TokenVerification, request: Request):
    db = request.app.mongodb
    normalized_email = data.email.lower()
    
    user = await db.users.find_one({
        "email": normalized_email,
        "reset_token": data.token
    })
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification code.")
        
    if user.get("reset_token_expires") < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification code has expired.")
        
    return {"message": "Verification successful."}


@router.post("/reset-password-v2")
async def reset_password_v2(data: PasswordReset, request: Request):
    db = request.app.mongodb
    normalized_email = data.email.lower()
    
    # 1. Check if passwords match
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    
    # 2. Verify token again for security
    user = await db.users.find_one({
        "email": normalized_email,
        "reset_token": data.token
    })
    
    if not user or user.get("reset_token_expires") < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired session.")
    
    # Update password and clear token
    hashed_pwd = get_password_hash(data.new_password)
    result = await db.users.update_one(
        {"email": normalized_email},
        {
            "$set": {"password": hashed_pwd, "is_verified": True},
            "$unset": {"reset_token": "", "reset_token_expires": ""}
        }
    )
    
    return {"message": "Password updated successfully!"}
