import math
from datetime import datetime, timedelta

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def is_donation_eligible(last_donation_date_str: str) -> bool:
    """
    Check if a donor is eligible (last donation > 90 days ago)
    """
    if not last_donation_date_str:
        return True
        
    try:
        # Assuming last_donation_date is stored as ISO string "YYYY-MM-DD"
        last_date = datetime.fromisoformat(last_donation_date_str)
        three_months_ago = datetime.utcnow() - timedelta(days=90)
        return last_date < three_months_ago
    except ValueError:
        return True
