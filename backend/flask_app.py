import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Send log messages to stdout so they show up in the Render logs
logging.basicConfig(level=logging.INFO)

from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from database.models import db, User, Trip, Activity, PackingItem, WeatherCache
from datetime import datetime, timedelta
from trip_functions import validate_data, validate_activities
from weather_functions import get_weather
from packing_functions import generate_packing_list

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "instance", "smartpack.db")

# In production DATABASE_URL variable points at the PostgreSQL database in the cloud
# For testing purposes we set it to an in-memory database (locally it falls back to SQLite)
database_url = os.environ.get("DATABASE_URL", f"sqlite:///{db_path}")

# Render gives PostgreSQL URLs as "postgres://" but SQLAlchemy needs "postgresql://"
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "smartpack-secret-key-change-in-production")

# Tokens last 8 hours so a user isn't logged out in the middle of using the app
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)

# The cloud platform (Neon) closes idle PostgreSQL connections. It leaves dead connections in the pool
# pool_pre_ping will test the connection before using it and replace it if it's dead
# pool_recycle retires connections after 5 minutes so they don't go stale
if database_url.startswith("postgresql://"):
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300
    }

db.init_app(app)
CORS(app)
JWTManager(app)

with app.app_context():
    db.create_all()

# Authentication methods

# Register a new user. We do basic input validation and save it to the database
@app.post("/auth/register")
def register():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"message": "Invalid data"}, 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not email or not password:
        return {"message": "Email and password are required"}, 400

    if len(password) < 6:
        return {"message": "Password must be at least 6 characters"}, 400

    if User.query.filter_by(email=email).first():
        return {"message": "An account with this email already exists"}, 409

    user = User(
        email=email,
        password_hash=generate_password_hash(password)
    )

    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))

    return {"token": token, "email": user.email}, 201

# Handle login and input validation
@app.post("/auth/login")
def login():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"message": "Invalid data"}, 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not email or not password:
        return {"message": "Email and password are required"}, 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return {"message": "Invalid email or password"}, 401

    token = create_access_token(identity=str(user.id))

    return {"token": token, "email": user.email}


# Trips methods

# Create new trip. Basic input validation and save to database
@app.post("/trips")
# Run a check before the code executes. This way we can check if the request is carrying a valid jwt (header, token etc). If not, the function won't run
@jwt_required()
def new_trip():
    # If we have a token, we check what user owns the jwt
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"message": "Invalid JSON data"}, 400

    trip_data, error = validate_data(data)

    if error:
        return {"message": error}, 400

    trip = Trip(
        destination=trip_data["destination"],
        luggage_type=trip_data["luggage_type"],
        start_date=trip_data["start_date"],
        end_date=trip_data["end_date"],
        user_id=user_id
    )

    db.session.add(trip)
    db.session.commit()

    return {"message": "Trip created", "id": trip.id}, 201

# Return all trips
@app.get("/trips")
@jwt_required()
def all_trips():
    user_id = int(get_jwt_identity())
    trips = Trip.query.filter_by(user_id=user_id).all()

    result = []

    for trip in trips:
        result.append({
            "id": trip.id,
            "destination": trip.destination,
            "luggage_type": trip.luggage_type,
            "start_date": trip.start_date,
            "end_date": trip.end_date
        })

    return result

# Return trip by id
@app.get("/trips/<int:id>")
@jwt_required()
def get_trip_by_id(id):
    user_id = int(get_jwt_identity())
    trip = db.session.get(Trip, id)

    if trip is None or trip.user_id != user_id:
        return {"message": "Trip not found"}, 404

    return {
        "id": trip.id,
        "destination": trip.destination,
        "luggage_type": trip.luggage_type,
        "start_date": trip.start_date,
        "end_date": trip.end_date
    }

# Update trip by id
@app.put("/trips/<int:id>")
@jwt_required()
def update_trip(id):
    user_id = int(get_jwt_identity())
    trip = db.session.get(Trip, id)

    if trip is None or trip.user_id != user_id:
        return {"message": "Trip not found"}, 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"message": "Invalid JSON data"}, 400

    trip_data, error = validate_data(data)

    if error:
        return {"message": error}, 400

    trip.destination = trip_data["destination"]
    trip.luggage_type = trip_data["luggage_type"]
    trip.start_date = trip_data["start_date"]
    trip.end_date = trip_data["end_date"]

    db.session.commit()

    return {
        "id": trip.id,
        "destination": trip.destination,
        "luggage_type": trip.luggage_type,
        "start_date": trip.start_date,
        "end_date": trip.end_date
    }

# Delete trip by id
@app.delete("/trips/<int:id>")
@jwt_required()
def delete_trip(id):
    user_id = int(get_jwt_identity())
    trip = db.session.get(Trip, id)

    if trip is None or trip.user_id != user_id:
        return {"message": "Trip not found"}, 404

    activities = Activity.query.filter_by(trip_id=id).all()
    for activity in activities:
        db.session.delete(activity)

    packing_items = PackingItem.query.filter_by(trip_id=id).all()
    for item in packing_items:
        db.session.delete(item)

    WeatherCache.query.filter_by(trip_id=id).delete()

    db.session.delete(trip)
    db.session.commit()

    return {"message": "Trip deleted successfully"}, 200


# Activities methods

# Return activities by trip
@app.get("/trips/<int:id>/activities")
@jwt_required()
def get_activities(id):
    user_id = int(get_jwt_identity())
    trip = db.session.get(Trip, id)

    if trip is None or trip.user_id != user_id:
        return {"message": "Trip not found"}, 404

    activities = Activity.query.filter_by(trip_id=id).all()

    return [{"id": a.id, "activity": a.activity} for a in activities]

# Create new activity inside a trip
@app.post("/trips/<int:id>/activities")
@jwt_required()
def add_activity(id):
    # If we have a token, we check what user owns the jwt
    user_id = int(get_jwt_identity())
    trip = db.session.get(Trip, id)

    if trip is None or trip.user_id != user_id:
        return {"message": "Trip not found"}, 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"message": "Invalid JSON data"}, 400

    activities, error = validate_activities(data)

    if error:
        return {"message": error}, 400

    for activity_name in activities:
        db.session.add(Activity(activity=activity_name, trip_id=id))

    db.session.commit()

    return {"message": "Activities added"}, 201

# Delete an activity
@app.delete("/trips/<int:id>/activities/<int:activity_id>")
@jwt_required()
def delete_activity(id, activity_id):
    user_id = int(get_jwt_identity())
    trip = db.session.get(Trip, id)

    if trip is None or trip.user_id != user_id:
        return {"message": "Trip not found"}, 404

    activity = db.session.get(Activity, activity_id)

    if activity is None or activity.trip_id != id:
        return {"message": "Activity not found"}, 404

    db.session.delete(activity)
    db.session.commit()

    return {"message": "Activity deleted successfully"}, 200


# Weather methods

# Returns saved weather for a trip (cached) or fetches it from the API and saves it
# The weather is cached because the cloud platform was causing the weather API to exceed fetch limits for free tier
# Returns a dict with an error key if the API call failed
def get_or_fetch_weather(trip):
    cache = WeatherCache.query.filter_by(trip_id=trip.id).first()

    if cache:
        return {
            "destination": cache.destination,
            "country": cache.country,
            "min_temperature": cache.min_temperature,
            "max_temperature": cache.max_temperature,
            "total_precipitation": cache.total_precipitation,
            "rain_expected": cache.rain_expected
        }

    weather = get_weather(trip.destination, trip.start_date, trip.end_date)

    if "error" in weather:
        return weather

    db.session.add(WeatherCache(
        destination=weather["destination"],
        country=weather["country"],
        min_temperature=weather["min_temperature"],
        max_temperature=weather["max_temperature"],
        total_precipitation=weather["total_precipitation"],
        rain_expected=weather["rain_expected"],
        trip_id=trip.id
    ))
    db.session.commit()

    return weather

# Get weather by trip
@app.get("/trips/<int:id>/weather")
@jwt_required()
def trip_weather(id):
    user_id = int(get_jwt_identity())
    trip = db.session.get(Trip, id)

    if trip is None or trip.user_id != user_id:
        return {"message": "Trip not found"}, 404

    # refresh will force a new API call. It clears the saved weather first
    if request.args.get("refresh") == "true":
        WeatherCache.query.filter_by(trip_id=id).delete()
        db.session.commit()

    weather = get_or_fetch_weather(trip)

    if "error" in weather:
        return weather, 400

    return weather


# Packing methods

# Get items by trip
@app.get("/trips/<int:id>/packing-list")
@jwt_required()
def get_packing_list(id):
    user_id = int(get_jwt_identity())
    trip = db.session.get(Trip, id)

    if trip is None or trip.user_id != user_id:
        return {"message": "Trip not found"}, 404

    existing_items = PackingItem.query.filter_by(trip_id=id).all()

    if existing_items:
        return {"items": [
            {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "quantity": item.quantity,
                "packed": item.packed,
                "reason": item.reason
            }
            for item in existing_items
        ]}

    activities = Activity.query.filter_by(trip_id=id).all()

    # We either get the cached weather value or we fetch it
    weather = get_or_fetch_weather(trip)

    if "error" in weather:
        return weather, 400

    packing_list = generate_packing_list(trip, activities, weather)

    for item in packing_list["items"]:
        db.session.add(PackingItem(
            name=item["name"],
            category=item["category"],
            quantity=item["quantity"],
            packed=False,
            reason=item["reason"],
            trip_id=id
        ))

    db.session.commit()

    return packing_list

# New packing list for the trip
@app.post("/trips/<int:trip_id>/packing-list")
@jwt_required()
def add_packing_item(trip_id):
    user_id = int(get_jwt_identity())
    trip = db.session.get(Trip, trip_id)

    if trip is None or trip.user_id != user_id:
        return {"message": "Trip not found"}, 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"message": "Invalid JSON data"}, 400

    name = data.get("name", "").strip()
    quantity = data.get("quantity", 1)

    if not name:
        return {"message": "Item name is required"}, 400

    if not isinstance(quantity, int) or quantity < 1:
        return {"message": "Quantity must be a positive number"}, 400

    item = PackingItem(
        name=name,
        category="Other",
        quantity=quantity,
        packed=False,
        reason="Added by user",
        trip_id=trip_id
    )

    db.session.add(item)
    db.session.commit()

    return {
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "quantity": item.quantity,
        "packed": item.packed,
        "reason": item.reason
    }, 201

# Delete packing list by trip
@app.delete("/trips/<int:trip_id>/packing-list")
@jwt_required()
def delete_packing_list(trip_id):
    user_id = int(get_jwt_identity())
    trip = db.session.get(Trip, trip_id)

    if trip is None or trip.user_id != user_id:
        return {"message": "Trip not found"}, 404

    for item in PackingItem.query.filter_by(trip_id=trip_id).all():
        db.session.delete(item)

    db.session.commit()

    return {"message": "List deleted successfully"}, 200

# Update packing list by trip
@app.patch("/trips/<int:trip_id>/packing-list/<int:item_id>")
@jwt_required()
def update_packing_item(trip_id, item_id):
    user_id = int(get_jwt_identity())
    trip = db.session.get(Trip, trip_id)

    if trip is None or trip.user_id != user_id:
        return {"message": "Trip not found"}, 404

    item = db.session.get(PackingItem, item_id)

    if item is None or item.trip_id != trip_id:
        return {"message": "Packing item not found"}, 404

    data = request.get_json()

    if "packed" in data:
        item.packed = data["packed"]

    db.session.commit()

    return {
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "quantity": item.quantity,
        "packed": item.packed,
        "reason": item.reason
    }

# Delete packing list by trip
@app.delete("/trips/<int:trip_id>/packing-list/<int:item_id>")
@jwt_required()
def delete_packing_item(trip_id, item_id):
    user_id = int(get_jwt_identity())
    trip = db.session.get(Trip, trip_id)

    if trip is None or trip.user_id != user_id:
        return {"message": "Trip not found"}, 404

    item = db.session.get(PackingItem, item_id)

    if item is None or item.trip_id != trip_id:
        return {"message": "Packing item not found"}, 404

    db.session.delete(item)
    db.session.commit()

    return {"message": "Item deleted successfully"}, 200

# Regenerate packing list in case the user changes dates, luggage type or wants to remove added items
@app.post("/trips/<int:trip_id>/packing-list/regenerate")
@jwt_required()
def regenerate_packing_list(trip_id):
    user_id = int(get_jwt_identity())
    trip = db.session.get(Trip, trip_id)

    if trip is None or trip.user_id != user_id:
        return {"message": "Trip not found"}, 404

    activities = Activity.query.filter_by(trip_id=trip_id).all()

    weather = get_or_fetch_weather(trip)

    if "error" in weather:
        return weather, 400

    packing_list = generate_packing_list(trip, activities, weather)

    for item in PackingItem.query.filter_by(trip_id=trip_id).all():
        if item.category != "Other":
            db.session.delete(item)

    for item in packing_list["items"]:
        db.session.add(PackingItem(
            name=item["name"],
            category=item["category"],
            quantity=item["quantity"],
            packed=False,
            reason=item["reason"],
            trip_id=trip_id
        ))

    db.session.commit()

    return {"message": "List regenerated successfully"}, 200


if __name__ == "__main__":
    app.run(debug=True)
