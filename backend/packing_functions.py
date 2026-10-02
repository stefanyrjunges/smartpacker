# Used some examples of activities to adapt the packing list according to its type

ACTIVITY_ITEMS = {
    "walking": [
        ("Comfortable trainers", "Footwear", 1),
        ("Day bag", "Accessories", 1),
    ],
    "sightseeing": [
        ("Comfortable trainers", "Footwear", 1),
        ("Day bag", "Accessories", 1),
    ],
    "hiking": [
        ("Hiking boots", "Footwear", 1),
        ("Hiking backpack", "Accessories", 1),
        ("Water bottle", "Accessories", 1),
    ],
    "trekking": [
        ("Hiking boots", "Footwear", 1),
        ("Hiking backpack", "Accessories", 1),
        ("Water bottle", "Accessories", 1),
    ],
    "swimming": [
        ("Swimwear", "Clothing", 2),
        ("Flip flops", "Footwear", 1),
        ("Beach towel", "Accessories", 1),
    ],
    "beach": [
        ("Swimwear", "Clothing", 2),
        ("Flip flops", "Footwear", 1),
        ("Beach towel", "Accessories", 1),
        ("Sunscreen", "Toiletries", 1),
    ],
    "sunbathing": [
        ("Swimwear", "Clothing", 2),
        ("Flip flops", "Footwear", 1),
        ("Sunscreen", "Toiletries", 1),
        ("Sun hat", "Accessories", 1),
    ],
    "nightlife": [
        ("Going-out outfit", "Clothing", 1),
        ("Dress shoes", "Footwear", 1),
    ],
    "clubbing": [
        ("Going-out outfit", "Clothing", 1),
        ("Dress shoes", "Footwear", 1),
    ],
    "skiing": [
        ("Ski jacket", "Clothing", 1),
        ("Ski trousers", "Clothing", 1),
        ("Thermal underlayer", "Clothing", 2),
        ("Ski gloves", "Accessories", 1),
        ("Ski goggles", "Accessories", 1),
        ("Ski socks", "Clothing", 3),
    ],
    "snowboarding": [
        ("Ski jacket", "Clothing", 1),
        ("Ski trousers", "Clothing", 1),
        ("Thermal underlayer", "Clothing", 2),
        ("Ski gloves", "Accessories", 1),
        ("Ski goggles", "Accessories", 1),
    ],
    "gym": [
        ("Sports kit", "Clothing", 2),
        ("Trainers", "Footwear", 1),
    ],
    "running": [
        ("Running shoes", "Footwear", 1),
        ("Sports kit", "Clothing", 2),
    ],
    "cycling": [
        ("Cycling shorts", "Clothing", 2),
        ("Helmet", "Accessories", 1),
    ],
    "camping": [
        ("Sleeping bag", "Accessories", 1),
        ("Tent", "Accessories", 1),
        ("Torch / headlamp", "Accessories", 1),
        ("Water bottle", "Accessories", 1),
    ],
    "photography": [
        ("Camera", "Electronics", 1),
        ("Camera charger", "Electronics", 1),
    ],
    "business": [
        ("Smart outfit", "Clothing", 2),
        ("Laptop", "Electronics", 1),
        ("Laptop charger", "Electronics", 1),
    ],
    "conference": [
        ("Smart outfit", "Clothing", 2),
        ("Laptop", "Electronics", 1),
        ("Notebook and pen", "Accessories", 1),
    ],
    "yoga": [
        ("Yoga mat", "Accessories", 1),
        ("Sports kit", "Clothing", 2),
    ],
    "diving": [
        ("Swimwear", "Clothing", 2),
        ("Underwater camera", "Electronics", 1),
    ],
    "fishing": [
        ("Fishing rod", "Accessories", 1),
        ("Waterproof jacket", "Clothing", 1),
        ("Sunscreen", "Toiletries", 1),
    ],
    "shopping": [
        ("Foldable tote bag", "Accessories", 1),
        ("Comfortable trainers", "Footwear", 1),
    ],
    "museum": [
        ("Comfortable trainers", "Footwear", 1),
        ("Day bag", "Accessories", 1),
    ],
    "concert": [
        ("Comfortable trainers", "Footwear", 1),
        ("Light jacket", "Clothing", 1),
    ],
}

# According to the weather and activities, generate the packing list

def generate_packing_list(trip, activities, weather):

    duration = (trip.end_date - trip.start_date).days + 1

    items = []

    # Basic items
    items.append({
        "name": "Underwear",
        "category": "Clothing",
        "quantity": duration,
        "reason": "Basic clothing"
    })
    items.append({
        "name": "Socks",
        "category": "Clothing",
        "quantity": duration,
        "reason": "Basic clothing"
    })
    items.append({
        "name": "T-shirts",
        "category": "Clothing",
        "quantity": duration,
        "reason": "Basic clothing"
    })

    # Essentials
    items.append({
        "name": "Phone charger",
        "category": "Essentials",
        "quantity": 1,
        "reason": "Travel essential"
    })
    items.append({
        "name": "Toiletries",
        "category": "Essentials",
        "quantity": 1,
        "reason": "Travel essential"
    })
    items.append({
        "name": "Travel documents",
        "category": "Essentials",
        "quantity": 1,
        "reason": "Passport, ID, tickets"
    })

    # Check what weather returned, then add items accordingly
    if weather["rain_expected"]:
        items.append({
            "name": "Rain jacket",
            "category": "Weather",
            "quantity": 1,
            "reason": "Rain expected"
        })
        items.append({
            "name": "Umbrella",
            "category": "Weather",
            "quantity": 1,
            "reason": "Rain expected"
        })

    if weather["min_temperature"] < 10:
        items.append({
            "name": "Warm jacket",
            "category": "Weather",
            "quantity": 1,
            "reason": "Cold temperatures expected"
        })
        items.append({
            "name": "Scarf",
            "category": "Weather",
            "quantity": 1,
            "reason": "Cold temperatures expected"
        })

    if weather["min_temperature"] < 5:
        items.append({
            "name": "Gloves",
            "category": "Weather",
            "quantity": 1,
            "reason": "Very cold temperatures expected"
        })

    if weather["max_temperature"] >= 20:
        items.append({
            "name": "Sunscreen",
            "category": "Weather",
            "quantity": 1,
            "reason": "Warm temperatures expected"
        })
        items.append({
            "name": "Sunglasses",
            "category": "Weather",
            "quantity": 1,
            "reason": "Warm temperatures expected"
        })

    added_names = {item["name"] for item in items}

    activity_names = [activity.activity.lower() for activity in activities]

    for activity_name in activity_names:
        if activity_name in ACTIVITY_ITEMS:
            for (name, category, quantity) in ACTIVITY_ITEMS[activity_name]:
                if name not in added_names:
                    items.append({
                        "name": name,
                        "category": category,
                        "quantity": quantity,
                        "reason": f"Added for {activity_name}"
                    })
                    added_names.add(name)

    if trip.luggage_type.lower() in ("carry-on", "backpack"):
        for item in items:
            if item["name"] in ("T-shirts", "Underwear", "Socks"):
                item["quantity"] = min(item["quantity"], 5)

    return {
        "duration": duration,
        "items": items
    }
