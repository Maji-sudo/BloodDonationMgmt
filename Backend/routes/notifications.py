from fastapi import APIRouter, HTTPException, status, Request
from bson import ObjectId
from datetime import datetime
from typing import List

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("/{user_email}")
async def get_notifications(user_email: str, request: Request):
    db = request.app.mongodb
    notifications = []
    async for n in db.notifications.find({"email": user_email.lower()}).sort("timestamp", -1).limit(50):
        n["id"] = str(n["_id"])
        del n["_id"]
        notifications.append(n)
    return notifications

@router.post("/read/{notif_id}")
async def mark_as_read(notif_id: str, request: Request):
    db = request.app.mongodb
    if not ObjectId.is_valid(notif_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
        
    await db.notifications.update_one({"_id": ObjectId(notif_id)}, {"$set": {"is_read": True}})
    return {"message": "Notification marked as read."}

@router.post("/read-all/{user_email}")
async def mark_all_as_read(user_email: str, request: Request):
    db = request.app.mongodb
    await db.notifications.update_many({"email": user_email.lower()}, {"$set": {"is_read": True}})
    return {"message": "All notifications marked as read."}

# Internal Helper for triggers
async def send_notification(db, email: str, title: str, message: str, n_type: str = "info", metadata: dict = None):
    notif = {
        "email": email.lower(),
        "title": title,
        "message": message,
        "type": n_type, # info, success, warning, danger
        "is_read": False,
        "timestamp": datetime.utcnow(),
        "metadata": metadata or {}
    }
    await db.notifications.insert_one(notif)
