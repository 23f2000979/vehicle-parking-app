from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    reserved_spots = db.relationship("ReservedSpot", back_populates="user", cascade="all, delete-orphan")

class ParkingLot(db.Model):
    __tablename__ = "parking_lots"
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(120), unique=True, nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    maximum_number_of_spots = db.Column(db.Integer, nullable=False)
    parking_spots = db.relationship("ParkingSpot", backref="parking_lot", cascade="all, delete-orphan")

class ParkingSpot(db.Model):
    __tablename__ = "parking_spots"
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey("parking_lots.id"), nullable=False)
    spot_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(1), nullable=False, default="A")
    reserved_spots = db.relationship("ReservedSpot", back_populates="parking_spot", cascade="all, delete-orphan")
    __table_args__ = (db.UniqueConstraint('lot_id', 'spot_number', name='_lot_spot_uc'),)

class ReservedSpot(db.Model):
    __tablename__ = "reserved_spots"
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey("parking_spots.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    parking_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    total_cost = db.Column(db.Float, nullable=True)
    user = db.relationship("User", back_populates="reserved_spots")
    parking_spot = db.relationship("ParkingSpot", back_populates="reserved_spots") 