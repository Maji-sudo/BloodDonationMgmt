from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/api/recipients", tags=["Recipients"])


# ──────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────

# Urgency: 1 = Low (surgery in 10 days)
#          2 = Medium (within 3 days)
#          3 = High / Critical (immediate)
UrgencyLevel = Literal[1, 2, 3]

URGENCY_LABELS = {
    1: "Low – Surgery scheduled in 10 days",
    2: "Medium – Blood required within 3 days",
    3: "Critical – Sudden accident/trauma, immediate requirement",
}


class BloodRequestCreate(BaseModel):
    patient_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+?[0-9]{7,15}$")
    blood_type: str = Field(..., pattern=r"^(A|B|AB|O)[+-]$|^Any$")
    units_needed: int = Field(..., ge=1, le=20)
    location: str = Field(..., min_length=3, max_length=300, description="Hospital name and city")
    urgency: UrgencyLevel = 1
    notes: Optional[str] = Field(None, max_length=500)


class BloodRequestUpdate(BaseModel):
    units_needed: Optional[int] = Field(None, ge=1, le=20)
    location: Optional[str] = None
    urgency: Optional[UrgencyLevel] = None
    is_fulfilled: Optional[bool] = None
    notes: Optional[str] = None


# ──────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────

def request_serializer(req: dict) -> dict:
    return {
        "id": str(req["_id"]),
        "patient_name": req["patient_name"],
        "email": req["email"],
        "phone": req["phone"],
        "blood_type": req["blood_type"],
        "units_needed": req["units_needed"],
        "location": req["location"],
        "urgency": req["urgency"],
        "urgency_label": URGENCY_LABELS.get(req["urgency"], "Unknown"),
        "is_fulfilled": req.get("is_fulfilled", False),
        "notes": req.get("notes"),
        "requested_at": str(req.get("requested_at", "")),
    }


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@router.post("/request", status_code=status.HTTP_201_CREATED)
async def create_blood_request(request_data: BloodRequestCreate, request: Request):
    """Submit a new blood request. Urgency: 1=Low, 2=Medium, 3=Critical."""
    db = request.app.mongodb

    req_dict = request_data.model_dump()
    req_dict["is_fulfilled"] = False
    req_dict["requested_at"] = datetime.utcnow()

    result = await db.blood_requests.insert_one(req_dict)
    created = await db.blood_requests.find_one({"_id": result.inserted_id})

    return {
        "message": "Blood request submitted successfully!",
        "urgency_label": URGENCY_LABELS[request_data.urgency],
        "request": request_serializer(created),
    }


@router.get("/", response_model=List[dict])
async def get_all_requests(
    request: Request,
    urgency: Optional[int] = None,
    fulfilled: Optional[bool] = None,
    blood_type: Optional[str] = None,
):
    """
    Get all blood requests. Optional filters:
    - ?urgency=3          → only critical requests
    - ?fulfilled=false    → only open requests
    - ?blood_type=O%2B    → only requests for O+
    """
    db = request.app.mongodb
    query = {}

    if urgency is not None:
        if urgency not in (1, 2, 3):
            raise HTTPException(status_code=400, detail="urgency must be 1, 2, or 3")
        query["urgency"] = urgency

    if fulfilled is not None:
        query["is_fulfilled"] = fulfilled

    if blood_type:
        query["blood_type"] = blood_type

    # Sort: Critical (3) first, then Medium (2), then Low (1), then by time
    results = []
    async for req in db.blood_requests.find(query).sort([("urgency", -1), ("requested_at", 1)]):
        results.append(request_serializer(req))

    return results


@router.get("/critical")
async def get_critical_requests(request: Request):
    """Shortcut to fetch only Level 3 (critical) unfulfilled requests."""
    db = request.app.mongodb
    results = []
    async for req in db.blood_requests.find(
        {"urgency": 3, "is_fulfilled": False}
    ).sort("requested_at", 1):
        results.append(request_serializer(req))

    return {
        "count": len(results),
        "critical_requests": results,
    }


@router.get("/{request_id}")
async def get_request_by_id(request_id: str, request: Request):
    """Get a single blood request by its ID."""
    db = request.app.mongodb

    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid request ID format.")

    req = await db.blood_requests.find_one({"_id": ObjectId(request_id)})
    if not req:
        raise HTTPException(status_code=404, detail="Blood request not found.")

    return request_serializer(req)


@router.patch("/{request_id}")
async def update_blood_request(request_id: str, updates: BloodRequestUpdate, request: Request):
    """Update a blood request — change urgency, units, or mark as fulfilled."""
    db = request.app.mongodb

    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid request ID format.")

    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided to update.")

    result = await db.blood_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Blood request not found.")

    updated = await db.blood_requests.find_one({"_id": ObjectId(request_id)})
    return {
        "message": "Blood request updated successfully.",
        "request": request_serializer(updated),
    }


@router.patch("/{request_id}/fulfill")
async def fulfill_request(request_id: str, request: Request):
    """Mark a blood request as fulfilled (blood has been donated)."""
    db = request.app.mongodb

    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid request ID format.")

    result = await db.blood_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"is_fulfilled": True, "fulfilled_at": datetime.utcnow()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Blood request not found.")

    return {"message": "Request marked as fulfilled. Thank you for saving a life! ❤️"}


@router.delete("/{request_id}", status_code=status.HTTP_200_OK)
async def delete_request(request_id: str, request: Request):
    """Delete a blood request."""
    db = request.app.mongodb

    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid request ID format.")

    result = await db.blood_requests.delete_one({"_id": ObjectId(request_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blood request not found.")

    return {"message": "Blood request deleted successfully."}
