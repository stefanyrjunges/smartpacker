from flask_sqlalchemy import SQLAlchemy

# Create the tables and rows of the database

db = SQLAlchemy()

# For authentication
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

# For each trip
class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.String(100), nullable=False)
    luggage_type = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    # Relate the trip to the user id so we know it belongs to a specific user
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

# For each activity inside the trip
class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity = db.Column(db.String(100), nullable=False)
    # Relate the activity to the trip id so we know it belongs to a specific trip
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)

# For the packing items for each trip
class PackingItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    packed = db.Column(db.Boolean, default=False, nullable=False)
    reason = db.Column(db.String(200))
    # Relate the item to the trip id so we know it belongs to a specific trip
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)

# Saved weather for a trip so we don't call the weather API every time
class WeatherCache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    min_temperature = db.Column(db.Float, nullable=False)
    max_temperature = db.Column(db.Float, nullable=False)
    total_precipitation = db.Column(db.Float, nullable=False)
    rain_expected = db.Column(db.Boolean, nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)
