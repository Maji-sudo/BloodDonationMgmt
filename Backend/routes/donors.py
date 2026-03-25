from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, date
from bson import ObjectId

router = APIRouter(prefix="/api/donors", tags=["Donors"])


# ──────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────

class DonorCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+?[0-9]{7,15}$")
    blood_type: str = Field(..., pattern=r"^(A|B|AB|O)[+-]$")
    age: int = Field(..., ge=18, le=65)
    weight: float = Field(..., ge=50.0, description="Weight in kg")
    last_donation_date: Optional[date] = None
    medical_conditions: Optional[str] = None
    address: Optional[str] = None
    lat: float = Field(0.0, description="Latitude for matching")
    lng: float = Field(0.0, description="Longitude for matching")
    is_available: bool = True


class DonorUpdate(BaseModel):
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{7,15}$")
    address: Optional[str] = None
    is_available: Optional[bool] = None
    last_donation_date: Optional[date] = None
    medical_conditions: Optional[str] = None


class DonorResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    blood_type: str
    age: int
    weight: float
    last_donation_date: Optional[str]
    medical_conditions: Optional[str]
    address: Optional[str]
    lat: float
    lng: float
    is_available: bool
    registered_at: str


# ──────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────

def donor_serializer(donor: dict) -> dict:
    return {
        "id": str(donor["_id"]),
        "name": donor["name"],
        "email": donor["email"],
        "phone": donor["phone"],
        "blood_type": donor["blood_type"],
        "age": donor["age"],
        "weight": donor["weight"],
        "last_donation_date": str(donor["last_donation_date"]) if donor.get("last_donation_date") else None,
        "medical_conditions": donor.get("medical_conditions"),
        "address": donor.get("address"),
        "lat": donor.get("lat", 0.0),
        "lng": donor.get("lng", 0.0),
        "is_available": donor.get("is_available", True),
        "registered_at": str(donor.get("registered_at", "")),
    }


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_donor(donor: DonorCreate, request: Request):
    """Register a new blood donor."""
    db = request.app.mongodb

    # Prevent duplicate email
    existing = await db.donors.find_one({"email": donor.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A donor with email '{donor.email}' is already registered."
        )

    donor_dict = donor.model_dump()
    donor_dict["registered_at"] = datetime.utcnow()

    # Convert date to string for MongoDB storage
    if donor_dict.get("last_donation_date"):
        donor_dict["last_donation_date"] = str(donor_dict["last_donation_date"])

    result = await db.donors.insert_one(donor_dict)
    created = await db.donors.find_one({"_id": result.inserted_id})

    return {
        "message": "Donor registered successfully!",
        "donor": donor_serializer(created)
    }


@router.get("/", response_model=List[DonorResponse])
async def get_all_donors(request: Request, available_only: bool = False):
    """Get all donors. Use ?available_only=true to filter."""
    db = request.app.mongodb
    query = {"is_available": True} if available_only else {}

    donors = []
    async for donor in db.donors.find(query):
        donors.append(donor_serializer(donor))

    return donors


@router.get("/search")
async def search_donors_by_blood_type(blood_type: str, request: Request):
    """Search available donors by blood type (e.g. /search?blood_type=O%2B)."""
    db = request.app.mongodb

    donors = []
    async for donor in db.donors.find({"blood_type": blood_type, "is_available": True}):
        donors.append(donor_serializer(donor))

    if not donors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No available donors found with blood type '{blood_type}'."
        )

    return {"blood_type": blood_type, "count": len(donors), "donors": donors}


@router.get("/{donor_id}")
async def get_donor_by_id(donor_id: str, request: Request):
    """Get a single donor by their ID."""
    db = request.app.mongodb

    if not ObjectId.is_valid(donor_id):
        raise HTTPException(status_code=400, detail="Invalid donor ID format.")

    donor = await db.donors.find_one({"_id": ObjectId(donor_id)})
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found.")

    return donor_serializer(donor)


@router.patch("/{donor_id}")
async def update_donor(donor_id: str, updates: DonorUpdate, request: Request):
    """Update donor availability, contact info, or last donation date."""
    db = request.app.mongodb

    if not ObjectId.is_valid(donor_id):
        raise HTTPException(status_code=400, detail="Invalid donor ID format.")

    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided to update.")

    if "last_donation_date" in update_data:
        update_data["last_donation_date"] = str(update_data["last_donation_date"])

    result = await db.donors.update_one(
        {"_id": ObjectId(donor_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Donor not found.")

    updated = await db.donors.find_one({"_id": ObjectId(donor_id)})
    return {"message": "Donor updated successfully.", "donor": donor_serializer(updated)}


@router.delete("/{donor_id}", status_code=status.HTTP_200_OK)
async def delete_donor(donor_id: str, request: Request):
    """Remove a donor from the system."""
    db = request.app.mongodb

    if not ObjectId.is_valid(donor_id):
        raise HTTPException(status_code=400, detail="Invalid donor ID format.")

    result = await db.donors.delete_one({"_id": ObjectId(donor_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Donor not found.")

    return {"message": "Donor deleted successfully."}


@router.get("/{donor_id}/requests")
async def get_recommended_requests_for_donor(donor_id: str, request: Request, limit: int = 10):
    """
    Get blood requests that match the donor's blood type and are nearby.
    """
    db = request.app.mongodb
    from utils import calculate_distance
    from routes.recipients import request_serializer

    if not ObjectId.is_valid(donor_id):
        raise HTTPException(status_code=400, detail="Invalid donor ID format.")

    donor = await db.donors.find_one({"_id": ObjectId(donor_id)})
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found.")

    # Find requests matching blood type (or Any) and not fulfilled
    requests_query = {
        "blood_type": {"$in": [donor["blood_type"], "Any"]},
        "is_fulfilled": False
    }
    
    nearby_requests = []
    async for req in db.blood_requests.find(requests_query):
        dist = calculate_distance(
            donor.get("lat", 0), donor.get("lng", 0),
            req.get("lat", 0), req.get("lng", 0)
        )
        # Filter by 10km radius
        if dist <= 10:
            req_data = request_serializer(req, viewer_email=donor["email"])
            req_data["distance_km"] = round(dist, 2)
            nearby_requests.append(req_data)

    # Sort: nearest first
    nearby_requests.sort(key=lambda x: x["distance_km"])
    return nearby_requests[:limit]


@router.post("/{donor_id}/accept/{blood_request_id}")
async def accept_blood_request(donor_id: str, blood_request_id: str, request: Request, screening_passed: bool = True):
    """
    Process a donor's decision to fulfill a specific blood request.
    Requires health screening verification.
    """
    db = request.app.mongodb
    if not screening_passed:
        raise HTTPException(status_code=400, detail="Health screening is mandatory before acceptance.")

    if not ObjectId.is_valid(donor_id) or not ObjectId.is_valid(blood_request_id):
         raise HTTPException(status_code=400, detail="Invalid ID format.")
    
    donor = await db.donors.find_one({"_id": ObjectId(donor_id)})
    blood_req = await db.blood_requests.find_one({"_id": ObjectId(blood_request_id)})
    
    if not donor or not blood_req:
        raise HTTPException(status_code=404, detail="Donor or Request not found.")
        
    # Check if already accepted
    existing = await db.blood_requests.find_one({
        "_id": ObjectId(blood_request_id),
        "matches.donor_id": donor_id
    })
    if existing:
        return {"message": "You have already accepted this request."}
        
    # Add donor to the request's matches (Accepted Donors)
    await db.blood_requests.update_one(
        {"_id": ObjectId(blood_request_id)},
        {"$push": {
            "matches": {
                "donor_id": donor_id,
                "email": donor["email"], # Storing email for privacy serializer lookup
                "name": donor["name"],
                "phone": donor["phone"],
                "blood_type": donor["blood_type"],
                "accepted_at": datetime.utcnow(),
                "screening_status": "Passed"
            }
        }}
    )
    
    # 3. Notify Recipient
    try:
        from routes.notifications import send_notification
        await send_notification(
            db, 
            blood_req["email"], 
            title="❤️ Lifesaver Found!", 
            message=f"{donor['name']} has accepted your request for {blood_req['blood_type']} blood.",
            n_type="success",
            metadata={"donor_id": donor_id, "request_id": blood_request_id}
        )
    except Exception as e:
        print(f"⚠️ NOTIFICATION ERROR: {str(e)}")
    
    return {"message": "Thank you for accepting! Your details are now visible to the recipient."}
