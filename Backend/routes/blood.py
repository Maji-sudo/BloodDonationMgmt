from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import Optional, List, cast
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/api/blood", tags=["Blood Inventory"])

# All valid blood types
BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

# Units below this threshold are considered LOW STOCK
LOW_STOCK_THRESHOLD = 5


# ──────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────

class InventoryCreate(BaseModel):
    blood_type: str = Field(..., pattern=r"^(A|B|AB|O)[+-]$")
    units_available: int = Field(..., ge=0)
    location: str = Field(..., min_length=2, max_length=200, description="Blood bank or hospital name")
    notes: Optional[str] = Field(None, max_length=300)


class InventoryUpdate(BaseModel):
    units_available: Optional[int] = Field(None, ge=0)
    location: Optional[str] = None
    notes: Optional[str] = None


class StockAdjustment(BaseModel):
    units: int = Field(..., ge=1, description="Number of units to add or subtract")
    reason: Optional[str] = Field(None, max_length=200, description="e.g. 'donation received', 'transfusion used'")


# ──────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────

def inventory_serializer(inv: dict) -> dict:
    units = inv.get("units_available", 0)
    return {
        "id": str(inv["_id"]),
        "blood_type": inv["blood_type"],
        "units_available": units,
        "location": inv["location"],
        "notes": inv.get("notes"),
        "stock_status": (
            "critical" if units == 0
            else "low" if units <= LOW_STOCK_THRESHOLD
            else "adequate"
        ),
        "last_updated": str(inv.get("last_updated", "")),
        "created_at": str(inv.get("created_at", "")),
    }


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@router.post("/inventory", status_code=status.HTTP_201_CREATED)
async def add_inventory_entry(data: InventoryCreate, request: Request):
    """Add a new blood inventory entry for a blood bank / hospital location."""
    db = request.app.mongodb

    # Prevent exact duplicate (same blood type + location)
    existing = await db.blood_inventory.find_one({
        "blood_type": data.blood_type,
        "location": data.location
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Inventory for '{data.blood_type}' at '{data.location}' already exists. Use PATCH to update units."
        )

    inv_dict = data.model_dump()
    inv_dict["created_at"] = datetime.utcnow()
    inv_dict["last_updated"] = datetime.utcnow()

    result = await db.blood_inventory.insert_one(inv_dict)
    created = await db.blood_inventory.find_one({"_id": result.inserted_id})

    return {
        "message": "Inventory entry created successfully!",
        "inventory": inventory_serializer(created),
    }


@router.get("/inventory", response_model=List[dict])
async def get_all_inventory(
    request: Request,
    blood_type: Optional[str] = None,
    status_filter: Optional[str] = None,  # "critical" | "low" | "adequate"
):
    """
    Get all blood inventory entries. Optional filters:
    - ?blood_type=O%2B     → only O+ entries
    - ?status_filter=low   → only low/critical stock
    """
    db = request.app.mongodb
    query = {}

    if blood_type:
        if blood_type not in BLOOD_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid blood type. Valid: {BLOOD_TYPES}")
        query["blood_type"] = blood_type

    results = []
    async for inv in db.blood_inventory.find(query).sort("blood_type", 1):
        serialized = inventory_serializer(inv)
        if status_filter and serialized["stock_status"] != status_filter:
            continue
        results.append(serialized)

    return results


@router.get("/summary")
async def get_inventory_summary(request: Request):
    """
    Aggregated summary of total units per blood type across all locations.
    Also flags which types are in critical/low supply.
    """
    db = request.app.mongodb

    total_units: dict[str, int] = {bt: 0 for bt in BLOOD_TYPES}
    location_counts: dict[str, int] = {bt: 0 for bt in BLOOD_TYPES}

    async for inv in db.blood_inventory.find({}):
        bt = inv.get("blood_type")
        if bt in total_units:
            total_units[bt] += inv.get("units_available", 0)
            location_counts[bt] += 1

    # Build summary with status
    summary = {}
    for bt in BLOOD_TYPES:
        units = total_units[bt]
        summary[bt] = {
            "total_units": units,
            "locations": location_counts[bt],
            "stock_status": (
                "critical" if units == 0
                else "low" if units <= LOW_STOCK_THRESHOLD
                else "adequate"
            ),
        }

    alerts = [bt for bt, d in summary.items() if d["stock_status"] in ("critical", "low")]

    return {
        "summary": summary,
        "low_stock_alert": alerts,
        "total_blood_types_tracked": sum(1 for d in summary.values() if int(d["locations"]) > 0),
    }


@router.get("/availability/{blood_type}")
async def check_availability(blood_type: str, request: Request):
    """Check total available units for a specific blood type across all locations."""
    db = request.app.mongodb

    if blood_type not in BLOOD_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid blood type. Valid types: {BLOOD_TYPES}")

    entries = []
    total = 0
    async for inv in db.blood_inventory.find({"blood_type": blood_type}):
        entries.append(inventory_serializer(inv))
        total += inv.get("units_available", 0)

    return {
        "blood_type": blood_type,
        "total_units": total,
        "stock_status": (
            "critical" if total == 0
            else "low" if total <= LOW_STOCK_THRESHOLD
            else "adequate"
        ),
        "locations": entries,
    }


@router.get("/inventory/{inventory_id}")
async def get_inventory_by_id(inventory_id: str, request: Request):
    """Get a single inventory entry by ID."""
    db = request.app.mongodb

    if not ObjectId.is_valid(inventory_id):
        raise HTTPException(status_code=400, detail="Invalid inventory ID format.")

    inv = await db.blood_inventory.find_one({"_id": ObjectId(inventory_id)})
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory entry not found.")

    return inventory_serializer(inv)


@router.patch("/inventory/{inventory_id}")
async def update_inventory(inventory_id: str, updates: InventoryUpdate, request: Request):
    """Directly update inventory fields (location, notes, or set exact units)."""
    db = request.app.mongodb

    if not ObjectId.is_valid(inventory_id):
        raise HTTPException(status_code=400, detail="Invalid inventory ID format.")

    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided to update.")

    update_data["last_updated"] = datetime.utcnow()

    result = await db.blood_inventory.update_one(
        {"_id": ObjectId(inventory_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Inventory entry not found.")

    updated = await db.blood_inventory.find_one({"_id": ObjectId(inventory_id)})
    return {"message": "Inventory updated.", "inventory": inventory_serializer(updated)}


@router.patch("/inventory/{inventory_id}/add")
async def add_units(inventory_id: str, adjustment: StockAdjustment, request: Request):
    """Add units to an inventory entry (e.g., after a donation is received)."""
    db = request.app.mongodb

    if not ObjectId.is_valid(inventory_id):
        raise HTTPException(status_code=400, detail="Invalid inventory ID format.")

    result = await db.blood_inventory.update_one(
        {"_id": ObjectId(inventory_id)},
        {
            "$inc": {"units_available": adjustment.units},
            "$set": {"last_updated": datetime.utcnow()}
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Inventory entry not found.")

    updated = await db.blood_inventory.find_one({"_id": ObjectId(inventory_id)})
    return {
        "message": f"✅ Added {adjustment.units} unit(s). Reason: {adjustment.reason or 'Not specified'}",
        "inventory": inventory_serializer(updated),
    }


@router.patch("/inventory/{inventory_id}/consume")
async def consume_units(inventory_id: str, adjustment: StockAdjustment, request: Request):
    """Subtract units from inventory (e.g., after a transfusion). Prevents going below 0."""
    db = request.app.mongodb

    if not ObjectId.is_valid(inventory_id):
        raise HTTPException(status_code=400, detail="Invalid inventory ID format.")

    inv = await db.blood_inventory.find_one({"_id": ObjectId(inventory_id)})
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory entry not found.")

    current = inv.get("units_available", 0)
    if adjustment.units > current:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Requested {adjustment.units} unit(s), only {current} available."
        )

    await db.blood_inventory.update_one(
        {"_id": ObjectId(inventory_id)},
        {
            "$inc": {"units_available": -adjustment.units},
            "$set": {"last_updated": datetime.utcnow()}
        }
    )

    updated = await db.blood_inventory.find_one({"_id": ObjectId(inventory_id)})
    return {
        "message": f"🩸 Consumed {adjustment.units} unit(s). Reason: {adjustment.reason or 'Not specified'}",
        "inventory": inventory_serializer(updated),
    }


@router.delete("/inventory/{inventory_id}", status_code=status.HTTP_200_OK)
async def delete_inventory_entry(inventory_id: str, request: Request):
    """Remove an inventory entry."""
    db = request.app.mongodb

    if not ObjectId.is_valid(inventory_id):
        raise HTTPException(status_code=400, detail="Invalid inventory ID format.")

    result = await db.blood_inventory.delete_one({"_id": ObjectId(inventory_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Inventory entry not found.")

    return {"message": "Inventory entry deleted successfully."}
