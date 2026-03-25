import os
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware
from database import connect_to_mongo, close_mongo_connection, db_instance

from routes.donors import router as donors_router
from routes.recipients import router as recipients_router
from routes.blood import router as blood_router
from routes.auth import router as auth_router

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB
    await connect_to_mongo()
    # Backward compatibility: Still attach to app for routes relying on request.app.mongodb
    app.mongodb_client = db_instance.client
    app.mongodb = db_instance.db
    yield
    # Shutdown: Close connection
    await close_mongo_connection()

app = FastAPI(
    title="Smart Blood Bank API",
    description="Backend services for blood donation management",
    version="1.0.0",
    lifespan=lifespan
)

# Setup CORS to allow requests from your React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ],  # Default Vite ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




from routes.auth import router as auth_router
from routes.notifications import router as notifications_router

# ── Register Routers ──────────────────────────
app.include_router(donors_router)
app.include_router(recipients_router)
app.include_router(blood_router)
app.include_router(auth_router)
app.include_router(notifications_router)


@app.get("/")
async def root():
    return {"message": "Welcome to the Smart Blood Bank API"}


@app.get("/api/health")
async def health_check():
    try:
        await db_instance.db.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    return {"status": "ok", "db_connection": db_status}
