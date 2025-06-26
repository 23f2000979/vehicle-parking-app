from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import datetime
import os

app = Flask(__name__, template_folder="templates")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///parking.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "supersecretkeyforvehicleparkingapp" 

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user") # 'admin' or 'user'
    reserved_spots = db.relationship("ReservedSpot", backref="user", cascade="all, delete-orphan")

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
    spot_number = db.Column(db.Integer, nullable=False) # e.g., 1, 2, 3... within a lot
    status = db.Column(db.String(1), nullable=False, default="A") # 'A' for Available, 'O' for Occupied
    reserved_spot_link = db.relationship("ReservedSpot", backref="parking_spot", uselist=False, cascade="all, delete-orphan") # One-to-one relationship

    __table_args__ = (db.UniqueConstraint('lot_id', 'spot_number', name='_lot_spot_uc'),)

class ReservedSpot(db.Model):
    __tablename__ = "reserved_spots"
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey("parking_spots.id"), unique=True, nullable=False) # One reserved spot per parking spot
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    parking_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    total_cost = db.Column(db.Float, nullable=True)

# Database Initialization and Admin Creation
with app.app_context():
    try:
        # Check if the database file exists, if not, it's a fresh start or it was deleted.
        # If it exists, we can choose to drop_all or not. For development, dropping all is common.
        # For production, you'd handle migrations.
        db_path = os.path.join(app.root_path, 'instance', 'parking.sqlite3')
        if os.path.exists(db_path):
            print("Database file exists. Dropping all tables for a clean start...")
            db.drop_all()
        else:
            print("Database file does not exist. Creating tables...")

        db.create_all()
        print("Creating admin account if not exists...")
        admin_available = User.query.filter_by(role="admin").first()
        if not admin_available:
            admin = User(
                email_id="admin@parking.com",
                password="admin", 
                full_name="Administrator",
                address="Admin Address",
                pin_code="000000",
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin account created.")
        else:
            print("Admin account already exists.")
        print("Database initialization complete.")
    except Exception as e:
        print(f"Error during database initialization: {e}")
        import traceback
        traceback.print_exc()

# --- Routes ---
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/user_register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        email_id = request.form["email_id"]
        password = request.form["password"]
        full_name = request.form["full_name"]
        address = request.form["address"]
        pin_code = request.form["pin_code"]

        existing_user = User.query.filter_by(email_id=email_id).first()
        if existing_user:
            flash("Email ID already registered. Please login or use a different email.", "danger")
            return redirect(url_for("user_register"))

        new_user = User(
            email_id=email_id,
            password=password, # NOTE: In a real application, hash this password!
            full_name=full_name,
            address=address,
            pin_code=pin_code,
            role="user"
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("user_login"))
    return render_template("user_register.html")

@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        email_id = request.form["email_id"]
        password = request.form["password"]
        user = User.query.filter_by(email_id=email_id, role="user").first()

        if user and user.password == password: # NOTE: In a real application, verify hashed password!
            # Clear any admin session keys
            session.pop("admin_logged_in", None)
            session.pop("admin_id", None)
            session["user_logged_in"] = True
            session["user_id"] = user.id
            session["user_email"] = user.email_id
            flash(f"Welcome, {user.full_name}!", "success")
            return redirect(url_for("user_dashboard"))
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("user_login"))
    return render_template("user_login.html")

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email_id = request.form["email_id"]
        password = request.form["password"]
        admin = User.query.filter_by(email_id=email_id, role="admin").first()

        if admin and admin.password == password:
            # Clear any user session keys
            session.pop("user_logged_in", None)
            session.pop("user_id", None)
            session.pop("user_email", None)
            session["admin_logged_in"] = True
            session["admin_id"] = admin.id
            flash("Welcome, Admin!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin credentials.", "danger")
            return redirect(url_for("admin_login"))
    return render_template("admin_login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)