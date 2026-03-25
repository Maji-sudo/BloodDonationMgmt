from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from datetime import datetime
from bson import ObjectId
from routes.auth import get_current_user

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
    lat: float = Field(0.0, description="Latitude for matching")
    lng: float = Field(0.0, description="Longitude for matching")
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

def request_serializer(req: dict, viewer_email: Optional[str] = None) -> dict:
    # Full data disclosure for authorized viewers (owner or nearby qualifying donor)
    # The filtering of 'who can see what' is now handled at the database query level
    return {
        "id": str(req["_id"]),
        "patient_name": req.get("patient_name", "Unknown"),
        "email": req.get("email"),
        "phone": req.get("phone"),
        "blood_type": req.get("blood_type", "Any"),
        "units_needed": req.get("units_needed", 1),
        "location": req.get("location", "Standard Hospital"),
        "urgency": req.get("urgency", 1),
        "is_fulfilled": req.get("is_fulfilled", False),
        "requested_at": str(req.get("requested_at", "")),
        "lat": req.get("lat", 0.0),
        "lng": req.get("lng", 0.0),
        "matches": req.get("matches", []),
        "notes": req.get("notes")
    }


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@router.post("/request", status_code=status.HTTP_201_CREATED)
async def create_blood_request(
    request_data: BloodRequestCreate, 
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Submit a new blood request. Urgency: 1=Low, 2=Medium, 3=Critical."""
    db = request.app.mongodb

    req_dict = request_data.model_dump()
    req_dict["is_fulfilled"] = False
    req_dict["requested_at"] = datetime.utcnow()
    req_dict["created_by"] = str(current_user["_id"]) # Formal ownership link
    req_dict["email"] = current_user["email"] # Ensure consistency

    # ── Update user role if not already recipient ──
    try:
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {"$set": {"role": "recipient"}}
        )
    except Exception as e:
        print(f"⚠️ ROLE UPDATE ERROR: {str(e)}")

    result = await db.blood_requests.insert_one(req_dict)
    
    # ── NOTIFY NEARBY DONORS ──────────────────────
    try:
        from routes.notifications import send_notification
        from utils import calculate_distance
        
        # Find all matching donors
        cursor = db.donors.find({
            "blood_type": {"$in": [request_data.blood_type, "Any"]},
            "is_available": True
        })
        
        async for d in cursor:
            dist = calculate_distance(
                request_data.lat, request_data.lng,
                d.get("lat", 0), d.get("lng", 0)
            )
            # If donor is within 10km, notify them
            if dist <= 10:
                await send_notification(
                    db, d["email"], 
                    title="🚨 Urgent Request Nearby",
                    message=f"Someone within {round(dist, 1)}km needs {request_data.blood_type} blood. Your help could save a life!",
                    n_type="warning",
                    metadata={"request_id": str(result.inserted_id)}
                )
    except Exception as e:
        print(f"⚠️ NOTIFICATION ERROR: {str(e)}")

    created = await db.blood_requests.find_one({"_id": result.inserted_id})
    return {"message": "Request submitted!", "request": request_serializer(created)}


@router.get("/", response_model=List[dict])
async def get_all_requests(
    request: Request,
    urgency: Optional[int] = None,
    fulfilled: Optional[bool] = None,
    blood_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all blood requests (STRICT OWNERSHIP RESTORED).
    Only the requests CREATED BY this specific user ID will be returned.
    """
    db = request.app.mongodb
    
    # Enforce absolute privacy: Filter by the authenticated user's ID or email
    query = {
        "$or": [
            {"created_by": str(current_user["_id"])},
            {"email": current_user["email"].lower()}
        ]
    }

    if urgency is not None:
        query["urgency"] = urgency
    if fulfilled is not None:
        query["is_fulfilled"] = fulfilled
    if blood_type:
        query["blood_type"] = blood_type

    results = []
    async for req in db.blood_requests.find(query).sort("requested_at", -1):
        results.append(request_serializer(req, viewer_email=current_user["email"]))
    
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
async def update_blood_request(
    request_id: str, 
    updates: BloodRequestUpdate, 
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Update a blood request — change urgency, units, or mark as fulfilled."""
    db = request.app.mongodb

    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid request ID format.")

    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided to update.")

    # Formal Ownership Enforcement: Only update if created_by matches current user
    result = await db.blood_requests.update_one(
        {"_id": ObjectId(request_id), "created_by": str(current_user["_id"])},
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
async def fulfill_request(
    request_id: str, 
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Mark a blood request as fulfilled (blood has been donated)."""
    db = request.app.mongodb

    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid request ID format.")

    result = await db.blood_requests.update_one(
        {"_id": ObjectId(request_id), "created_by": str(current_user["_id"])},
        {"$set": {"is_fulfilled": True, "fulfilled_at": datetime.utcnow()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Blood request not found.")

    return {"message": "Request marked as fulfilled. Thank you for saving a life! ❤️"}


@router.delete("/{request_id}", status_code=status.HTTP_200_OK)
async def delete_request(
    request_id: str, 
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Delete a blood request."""
    db = request.app.mongodb

    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid request ID format.")

    result = await db.blood_requests.delete_one({
        "_id": ObjectId(request_id), 
        "created_by": str(current_user["_id"])
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blood request not found.")

    return {"message": "Blood request deleted successfully."}


@router.post("/{request_id}/auto-allocate")
async def auto_allocate_donors(
    request_id: str, 
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Core Logic: 
    1. Find eliigible donors (blood type, distance, cooldown).
    2. Shortlist based on distance.
    3. Allocate up to units_needed.
    4. Handle partial donation (reduce units_needed).
    5. Mark donor as unavailable.
    """
    db = request.app.mongodb
    from utils import calculate_distance, is_donation_eligible
    from routes.donors import donor_serializer

    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid request ID format.")

    # 1. Get the request
    blood_req = await db.blood_requests.find_one({"_id": ObjectId(request_id)})
    if not blood_req or blood_req.get("is_fulfilled"):
        raise HTTPException(status_code=404, detail="Open blood request not found.")

    # 🔒 Ownership Check: Only the requester can auto-allocate donors
    # Compare with both email AND internal ID if possible
    if str(blood_req.get("created_by")) != str(current_user["_id"]) and blood_req.get("email") != current_user["email"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the original requester can trigger auto-allocation.")

    units_needed = blood_req.get("units_needed", 0)
    blood_type = blood_req.get("blood_type")
    
    # 2. Get potential donors
    potential_donors = []
    donors_query = {"blood_type": blood_type, "is_available": True}
    
    async for d in db.donors.find(donors_query):
        if is_donation_eligible(d.get("last_donation_date")):
            dist = calculate_distance(
                blood_req.get("lat", 0), blood_req.get("lng", 0),
                d.get("lat", 0), d.get("lng", 0)
            )
            potential_donors.append({
                "id": str(d["_id"]),
                "name": d.get("name"),
                "phone": d.get("phone"),
                "distance": dist
            })

    # 3. Sort by distance (minimum distance first)
    potential_donors.sort(key=lambda x: x["distance"])

    # 4. Allocate
    allocated_count = 0
    allocations = blood_req.get("allocations", [])
    
    for donor in potential_donors:
        if units_needed <= 0:
            break
            
        # Allocate this donor
        allocated_count += 1
        units_needed -= 1
        
        # Mark donor as unavailable and set last donation date
        await db.donors.update_one(
            {"_id": ObjectId(donor["id"])},
            {"$set": {
                "is_available": False,
                "last_donation_date": datetime.utcnow().strftime("%Y-%m-%d")
            }}
        )
        
        allocations.append({
            "donor_id": donor["id"],
            "donor_name": donor["name"],
            "donor_phone": donor["phone"],
            "allocated_at": datetime.utcnow()
        })

    # 5. Update request
    is_fulfilled = (units_needed <= 0)
    await db.blood_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {
            "units_needed": units_needed,
            "is_fulfilled": is_fulfilled,
            "allocations": allocations,
            "fulfilled_at": datetime.utcnow() if is_fulfilled else None
        }}
    )

    return {
        "status": "partial" if not is_fulfilled and allocated_count > 0 else "success" if is_fulfilled else "no_matches",
        "allocated_units": allocated_count,
        "remaining_units": units_needed,
        "is_fulfilled": is_fulfilled,
        "allocations": allocations[-allocated_count:] if allocated_count > 0 else []
    }

@router.get("/{request_id}/matches")
async def match_best_donors(
    request_id: str, 
    request: Request, 
    limit: int = 5,
    current_user: dict = Depends(get_current_user)
):
    """
    Find best donors for a request WITHOUT allocating them.
    Used for previewing matches in the UI.
    🔒 Protected: User ID must match created_by or email.
    """
    db = request.app.mongodb
    from utils import calculate_distance, is_donation_eligible
    from routes.donors import donor_serializer

    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid request ID format.")

    blood_req = await db.blood_requests.find_one({"_id": ObjectId(request_id)})
    if not blood_req:
        raise HTTPException(status_code=404, detail="Blood request not found.")

    # 🔒 Ownership Check
    if str(blood_req.get("created_by")) != str(current_user["_id"]) and blood_req.get("email") != current_user["email"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. You do not own this request.")

    donors_query = {"blood_type": blood_req["blood_type"], "is_available": True}
    
    potential_donors = []
    async for d in db.donors.find(donors_query):
        if is_donation_eligible(d.get("last_donation_date")):
            dist = calculate_distance(
                blood_req.get("lat", 0), blood_req.get("lng", 0),
                d.get("lat", 0), d.get("lng", 0)
            )
            donor_data = donor_serializer(d)
            donor_data["distance_km"] = round(dist, 2)
            potential_donors.append(donor_data)

    potential_donors.sort(key=lambda x: x["distance_km"])
    return {
        "request_id": request_id,
        "matches_count": len(potential_donors),
        "matches": potential_donors[:limit]
    }

