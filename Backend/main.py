import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI(
    title="Smart Blood Bank API",
    description="Backend services for blood donation management",
    version="1.0.0"
)

# Setup CORS to allow requests from your React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"], # Default Vite ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup (Motor for Async MongoDB)
MONGO_URI="mongodb+srv://majinmandramoorthy2007_db_user:NKgHuUH9MdHvly4A@aetherblood.mne7vso.mongodb.net/?appName=AetherBlood"
client = AsyncIOMotorClient(MONGO_URI)
db = client.bloodbank

@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = client
    app.mongodb = db

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

@app.get("/")
async def root():
    return {"message": "Welcome to the Smart Blood Bank API"}

@app.get("/api/health")
async def health_check():
    # Simple ping to verify DB connection
    try:
        await db.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = "disconnected"
    return {"status": "ok", "db_connection": db_status}
