import asyncio
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

MONGO_URI = "mongodb+srv://majinmandramoorthy2007_db_user:NKgHuUH9MdHvly4A@aetherblood.mne7vso.mongodb.net/?appName=AetherBlood"

# Chennai GPS coordinates (realistic, walkable distances)
LOCATIONS = [
    (13.0827, 80.2707, "Chennai General Hospital"),
    (13.0067, 80.2206, "Apollo Medical Center"),
    (12.9171, 80.1923, "Global Health City"),
    (13.0405, 80.2337, "MIOT International"),
    (12.9229, 80.1275, "Tambaram Medical College"),
]

async def seed():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.bloodbank

    print("Cleaning old data...")
    await db.donors.delete_many({})
    await db.blood_requests.delete_many({})
    await db.users.delete_many({})
    await db.notifications.delete_many({})

    print("Creating test users...")
    hashed_pwd = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
    verify_ok = bcrypt.checkpw(b"password123", hashed_pwd.encode())
    print(f"  Hash verify test: {'PASS' if verify_ok else 'FAIL'}")

    r = await db.users.insert_one({
        "email": "test@example.com", "password": hashed_pwd,
        "full_name": "Test Recipient", "role": "recipient",
        "is_verified": True, "created_at": datetime.utcnow()
    })
    await db.users.insert_one({
        "email": "donor@example.com", "password": hashed_pwd,
        "full_name": "Test Donor", "role": "donor",
        "is_verified": True, "created_at": datetime.utcnow()
    })

    print("Creating 10 donors...")
    # Donors are placed AT or VERY NEAR the same hospitals as the requests
    # so distance matching is guaranteed to work
    donors = [
        # Donor 1 — our test account, O+ at Chennai General (request 1 is O+, same location)
        {"name": "Test Donor",    "email": "donor@example.com",   "blood_type": "O+",
         "lat": 13.0827, "lng": 80.2707, "phone": "+919000000001", "age": 28, "weight": 70.0,
         "last_donation_date": (datetime.now()-timedelta(days=150)).strftime("%Y-%m-%d"),
         "is_available": True, "registered_at": datetime.utcnow()},

        {"name": "Arjun Kumar",   "email": "arjun@test.com",      "blood_type": "A+",
         "lat": 13.0080, "lng": 80.2220, "phone": "+919111111111", "age": 30, "weight": 72.0,
         "last_donation_date": (datetime.now()-timedelta(days=120)).strftime("%Y-%m-%d"),
         "is_available": True, "registered_at": datetime.utcnow()},

        {"name": "Priya Sharma",  "email": "priya@test.com",      "blood_type": "B+",
         "lat": 12.9200, "lng": 80.1940, "phone": "+919222222222", "age": 25, "weight": 60.0,
         "last_donation_date": (datetime.now()-timedelta(days=100)).strftime("%Y-%m-%d"),
         "is_available": True, "registered_at": datetime.utcnow()},

        {"name": "Ravi Krishnan", "email": "ravi@test.com",       "blood_type": "AB+",
         "lat": 13.0400, "lng": 80.2340, "phone": "+919333333333", "age": 35, "weight": 80.0,
         "last_donation_date": (datetime.now()-timedelta(days=200)).strftime("%Y-%m-%d"),
         "is_available": True, "registered_at": datetime.utcnow()},

        {"name": "Meena Raj",     "email": "meena@test.com",      "blood_type": "O-",
         "lat": 12.9230, "lng": 80.1290, "phone": "+919444444444", "age": 27, "weight": 57.0,
         "last_donation_date": (datetime.now()-timedelta(days=180)).strftime("%Y-%m-%d"),
         "is_available": True, "registered_at": datetime.utcnow()},

        {"name": "Siva Prasad",   "email": "siva@test.com",       "blood_type": "O+",
         "lat": 13.0850, "lng": 80.2750, "phone": "+919555555555", "age": 32, "weight": 75.0,
         "last_donation_date": (datetime.now()-timedelta(days=95)).strftime("%Y-%m-%d"),
         "is_available": True, "registered_at": datetime.utcnow()},

        {"name": "Lakshmi Devi",  "email": "laxmi@test.com",      "blood_type": "A+",
         "lat": 13.0050, "lng": 80.2200, "phone": "+919666666666", "age": 29, "weight": 63.0,
         "last_donation_date": (datetime.now()-timedelta(days=131)).strftime("%Y-%m-%d"),
         "is_available": True, "registered_at": datetime.utcnow()},

        {"name": "Dinesh Babu",   "email": "dinesh@test.com",     "blood_type": "B+",
         "lat": 12.9180, "lng": 80.1930, "phone": "+919777777777", "age": 40, "weight": 83.0,
         "last_donation_date": (datetime.now()-timedelta(days=160)).strftime("%Y-%m-%d"),
         "is_available": True, "registered_at": datetime.utcnow()},

        {"name": "Kavitha S",     "email": "kavitha@test.com",    "blood_type": "AB+",
         "lat": 13.0900, "lng": 80.2800, "phone": "+919888888888", "age": 23, "weight": 55.0,
         "last_donation_date": (datetime.now()-timedelta(days=110)).strftime("%Y-%m-%d"),
         "is_available": True, "registered_at": datetime.utcnow()},

        {"name": "Surya Nathan",  "email": "surya@test.com",      "blood_type": "O+",
         "lat": 13.0300, "lng": 80.2500, "phone": "+919999999990", "age": 38, "weight": 88.0,
         "last_donation_date": (datetime.now()-timedelta(days=145)).strftime("%Y-%m-%d"),
         "is_available": True, "registered_at": datetime.utcnow()},
    ]
    await db.donors.insert_many(donors)
    print(f"  Inserted {len(donors)} donors")

    print("Creating 10 blood requests...")
    # Requests are placed at the SAME coordinates as the hospitals where donors are
    # So the distance calculation will show short distances (< 3km)
    requests = [
        {"patient_name": "Patient 1",  "email": "test@example.com", "created_by": str(r.inserted_id),
         "phone": "+919911111111", "blood_type": "O+",  "units_needed": 2,
         "location": "Chennai General Hospital", "lat": 13.0827, "lng": 80.2707,
         "urgency": 3, "is_fulfilled": False, "notes": "Critical accident case",
         "requested_at": datetime.utcnow() - timedelta(hours=1)},

        {"patient_name": "Patient 2",  "email": "test@example.com", "created_by": str(r.inserted_id),
         "phone": "+919922222222", "blood_type": "A+",  "units_needed": 1,
         "location": "Apollo Medical Center", "lat": 13.0067, "lng": 80.2206,
         "urgency": 2, "is_fulfilled": False, "notes": "Surgery scheduled tomorrow",
         "requested_at": datetime.utcnow() - timedelta(hours=3)},

        {"patient_name": "Patient 3",  "email": "test@example.com", "created_by": str(r.inserted_id),
         "phone": "+919933333333", "blood_type": "B+",  "units_needed": 3,
         "location": "Global Health City", "lat": 12.9171, "lng": 80.1923,
         "urgency": 1, "is_fulfilled": False, "notes": "Cancer treatment",
         "requested_at": datetime.utcnow() - timedelta(hours=5)},

        {"patient_name": "Patient 4",  "email": "test@example.com", "created_by": str(r.inserted_id),
         "phone": "+919944444444", "blood_type": "AB+", "units_needed": 2,
         "location": "MIOT International", "lat": 13.0405, "lng": 80.2337,
         "urgency": 3, "is_fulfilled": False, "notes": "Post-op blood loss",
         "requested_at": datetime.utcnow() - timedelta(hours=2)},

        {"patient_name": "Patient 5",  "email": "test@example.com", "created_by": str(r.inserted_id),
         "phone": "+919955555555", "blood_type": "O-",  "units_needed": 4,
         "location": "Tambaram Medical College", "lat": 12.9229, "lng": 80.1275,
         "urgency": 2, "is_fulfilled": False, "notes": "Universal blood needed urgently",
         "requested_at": datetime.utcnow() - timedelta(hours=8)},

        {"patient_name": "Patient 6",  "email": "test@example.com", "created_by": str(r.inserted_id),
         "phone": "+919966666666", "blood_type": "A+",  "units_needed": 1,
         "location": "Apollo Medical Center", "lat": 13.0070, "lng": 80.2210,
         "urgency": 1, "is_fulfilled": False, "notes": "Dialysis patient",
         "requested_at": datetime.utcnow() - timedelta(hours=10)},

        {"patient_name": "Patient 7",  "email": "test@example.com", "created_by": str(r.inserted_id),
         "phone": "+919977777777", "blood_type": "O+",  "units_needed": 2,
         "location": "Chennai General Hospital", "lat": 13.0830, "lng": 80.2710,
         "urgency": 2, "is_fulfilled": False, "notes": "Emergency delivery complication",
         "requested_at": datetime.utcnow() - timedelta(hours=4)},

        {"patient_name": "Patient 8",  "email": "test@example.com", "created_by": str(r.inserted_id),
         "phone": "+919988888888", "blood_type": "B+",  "units_needed": 2,
         "location": "Global Health City", "lat": 12.9175, "lng": 80.1925,
         "urgency": 3, "is_fulfilled": False, "notes": "Thalassemia patient",
         "requested_at": datetime.utcnow() - timedelta(hours=2)},

        {"patient_name": "Patient 9",  "email": "test@example.com", "created_by": str(r.inserted_id),
         "phone": "+919991111111", "blood_type": "AB+", "units_needed": 1,
         "location": "MIOT International", "lat": 13.0410, "lng": 80.2340,
         "urgency": 1, "is_fulfilled": False, "notes": "Elective surgery",
         "requested_at": datetime.utcnow() - timedelta(hours=20)},

        {"patient_name": "Patient 10", "email": "test@example.com", "created_by": str(r.inserted_id),
         "phone": "+919999001001", "blood_type": "O+",  "units_needed": 3,
         "location": "Tambaram Medical College", "lat": 12.9235, "lng": 80.1280,
         "urgency": 3, "is_fulfilled": False, "notes": "Trauma victim - URGENT",
         "requested_at": datetime.utcnow() - timedelta(hours=1)},
    ]
    await db.blood_requests.insert_many(requests)
    print(f"  Inserted {len(requests)} requests")

    print("\nAll done!")
    print("Recipient: test@example.com / password123")
    print("Donor:     donor@example.com / password123")
    print("\nExpected distance results:")
    print("  Patient 1 (O+ @ Chennai General) -> Test Donor (O+, same loc) ~0km")
    print("  Patient 1 (O+ @ Chennai General) -> Siva Prasad (O+, ~0.5km away) ~0.5km")
    print("  Patient 2 (A+ @ Apollo)          -> Arjun Kumar (A+, same loc) ~0.2km")

asyncio.run(seed())
