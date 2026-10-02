import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from database.models import db, User, Trip, Activity, PackingItem
from datetime import datetime
from trip_functions import validate_data, validate_activities
from weather_functions import get_weather
from packing_functions import generate_packing_list

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "instance", "smartpack.db")

# In production DATABASE_URL points at the cloud PostgreSQL database.
# Tests set it to an in-memory database. Locally it falls back to SQLite.
database_url = os.environ.get("DATABASE_URL", f"sqlite:///{db_path}")

# Render gives PostgreSQL URLs as "postgres://" but SQLAlchemy needs "postgresql://"
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "smartpack-secret-key-change-in-production")

db.init_app(app)
CORS(app)
JWTManager(app)

with app.app_context():
    db.create_all()

# Authentication methods

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

@app.post("/trips")
@jwt_required()
def new_trip():
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

    db.session.delete(trip)
    db.session.commit()

    return {"message": "Trip deleted successfully"}, 200


# Activities methods

@app.get("/trips/<int:id>/activities")
@jwt_required()
def get_activities(id):
    user_id = int(get_jwt_identity())
    trip = db.session.get(Trip, id)

    if trip is None or trip.user_id != user_id:
        return {"message": "Trip not found"}, 404

    activities = Activity.query.filter_by(trip_id=id).all()

    return [{"id": a.id, "activity": a.activity} for a in activities]


@app.post("/trips/<int:id>/activities")
@jwt_required()
def add_activity(id):
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

@app.get("/trips/<int:id>/weather")
@jwt_required()
def trip_weather(id):
    user_id = int(get_jwt_identity())
    trip = db.session.get(Trip, id)

    if trip is None or trip.user_id != user_id:
        return {"message": "Trip not found"}, 404

    weather = get_weather(trip.destination, trip.start_date, trip.end_date)

    return weather


# Packing methods

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

    weather = get_weather(trip.destination, trip.start_date, trip.end_date)

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


@app.post("/trips/<int:trip_id>/packing-list/regenerate")
@jwt_required()
def regenerate_packing_list(trip_id):
    user_id = int(get_jwt_identity())
    trip = db.session.get(Trip, trip_id)

    if trip is None or trip.user_id != user_id:
        return {"message": "Trip not found"}, 404

    activities = Activity.query.filter_by(trip_id=trip_id).all()

    weather = get_weather(trip.destination, trip.start_date, trip.end_date)

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
