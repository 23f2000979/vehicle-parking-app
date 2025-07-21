from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import datetime
import os

app = Flask(__name__, template_folder="templates")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///parking.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "supersecretkeyforvehicleparkingapp") # Use environment variable in production

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
    reserved_spots = db.relationship("ReservedSpot", backref="parking_spot", cascade="all, delete-orphan") # One-to-many relationship

    __table_args__ = (db.UniqueConstraint('lot_id', 'spot_number', name='_lot_spot_uc'),)

class ReservedSpot(db.Model):
    __tablename__ = "reserved_spots"
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey("parking_spots.id"), nullable=False) # Remove unique=True
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
            print("Database file exists.")
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

@app.route("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "message": "Vehicle Parking App is running"}, 200

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

# User Dashboard
@app.route("/user_dashboard", methods=["GET"])
def user_dashboard():
    if "user_logged_in" not in session:
        flash("Please login to access your dashboard.", "danger")
        return redirect(url_for("user_login"))

    search_query = request.args.get('query', '').strip()
    
    all_parking_lots = db.session.query(ParkingLot).all()
    parking_lots_data = []

    for lot in all_parking_lots:
        total_spots = db.session.query(ParkingSpot).filter_by(lot_id=lot.id).count()
        available_spots = db.session.query(ParkingSpot).filter_by(lot_id=lot.id, status="A").count()
        
        # Apply search filter based on prime_location_name, address, or pin_code
        if not search_query or \
           search_query.lower() in lot.prime_location_name.lower() or \
           search_query.lower() in lot.address.lower() or \
           search_query.lower() in lot.pin_code.lower():
            
            parking_lots_data.append({
                'lot': lot,
                'total_spots': total_spots,
                'available_spots': available_spots
            })
    
    # Sort parking_lots_data (e.g., by prime_location_name)
    parking_lots_data.sort(key=lambda x: x['lot'].prime_location_name.lower())

    # Fetch data for user parking summary chart
    user_id = session.get("user_id")
    parking_history_for_chart = []
    if user_id:
        monthly_costs = db.session.query(
            db.func.strftime('%Y-%m', ReservedSpot.parking_timestamp).label('month'),
            db.func.sum(ReservedSpot.total_cost).label('total_cost')
        ).filter(
            ReservedSpot.user_id == user_id, 
            ReservedSpot.total_cost.isnot(None)
        ).group_by('month').order_by('month').all()
        
        for item in monthly_costs:
            parking_history_for_chart.append({'month': item.month, 'total_cost': item.total_cost})

    return render_template("user_dashboard.html", 
                           parking_lots_data=parking_lots_data,
                           parking_data_for_chart=parking_history_for_chart,
                           query=search_query)

# Admin Dashboard
@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin_logged_in" not in session:
        flash("Please login to access the admin dashboard.", "danger")
        return redirect(url_for("admin_login"))
    return render_template("admin_dashboard.html")

# Admin - Parking Lot Management Routes
@app.route("/admin_parking_lots", methods=["GET", "POST"])
def admin_parking_lots():
    if "admin_logged_in" not in session:
        flash("Please login to access the admin dashboard.", "danger")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        prime_location_name = request.form["prime_location_name"].strip()
        price_per_hour = float(request.form["price_per_hour"])
        address = request.form["address"].strip()
        pin_code = request.form["pin_code"].strip()
        maximum_number_of_spots = int(request.form["maximum_number_of_spots"])

        if not prime_location_name or not address or not pin_code:
            flash("All fields are required.", "danger")
            return redirect(url_for("admin_parking_lots"))
        if not (0 < price_per_hour):
            flash("Price per hour must be positive.", "danger")
            return redirect(url_for("admin_parking_lots"))
        if not (maximum_number_of_spots > 0):
            flash("Maximum number of spots must be at least 1.", "danger")
            return redirect(url_for("admin_parking_lots"))

        existing_lot = db.session.query(ParkingLot).filter(db.func.lower(ParkingLot.prime_location_name) == db.func.lower(prime_location_name)).first()
        if existing_lot:
            flash("A parking lot with this name already exists.", "danger")
            return redirect(url_for("admin_parking_lots"))

        new_lot = ParkingLot(
            prime_location_name=prime_location_name,
            price_per_hour=price_per_hour,
            address=address,
            pin_code=pin_code,
            maximum_number_of_spots=maximum_number_of_spots
        )
        db.session.add(new_lot)
        db.session.commit()

        # Create parking spots for the new lot
        for i in range(1, maximum_number_of_spots + 1):
            spot = ParkingSpot(lot_id=new_lot.id, spot_number=i, status="A")
            db.session.add(spot)
        db.session.commit()

        flash("Parking Lot added successfully!", "success")
        return redirect(url_for("admin_parking_lots"))

    parking_lots = db.session.query(ParkingLot).order_by(ParkingLot.prime_location_name).all()
    lot_data = []
    for lot in parking_lots:
        total_spots = db.session.query(ParkingSpot).filter_by(lot_id=lot.id).count()
        occupied_spots = db.session.query(ParkingSpot).filter_by(lot_id=lot.id, status="O").count()
        spots_in_lot = db.session.query(ParkingSpot).filter_by(lot_id=lot.id).order_by(ParkingSpot.spot_number).all()
        lot_data.append({
            'lot': lot,
            'total_spots': total_spots,
            'occupied_spots': occupied_spots,
            'spots_list': spots_in_lot
        })

    return render_template("admin_parking_lots.html", lot_data=lot_data)

@app.route("/admin_edit_parking_lot/<int:lot_id>", methods=["GET", "POST"])
def admin_edit_parking_lot(lot_id):
    if "admin_logged_in" not in session:
        flash("Please login to access the admin dashboard.", "danger")
        return redirect(url_for("admin_login"))

    lot = db.session.query(ParkingLot).get_or_404(lot_id)

    if request.method == "POST":
        new_prime_location_name = request.form["prime_location_name"].strip()
        price_per_hour = float(request.form["price_per_hour"])
        address = request.form["address"].strip()
        pin_code = request.form["pin_code"].strip()
        new_max_spots = int(request.form["maximum_number_of_spots"])

        if not new_prime_location_name or not address or not pin_code:
            flash("All fields are required.", "danger")
            return redirect(url_for("admin_edit_parking_lot", lot_id=lot.id))
        if not (0 < price_per_hour):
            flash("Price per hour must be positive.", "danger")
            return redirect(url_for("admin_edit_parking_lot", lot_id=lot.id))
        if not (new_max_spots > 0):
            flash("Maximum number of spots must be at least 1.", "danger")
            return redirect(url_for("admin_edit_parking_lot", lot_id=lot.id))

        # Check for duplicate name, excluding current lot
        existing_lot_with_name = db.session.query(ParkingLot).filter(
            db.func.lower(ParkingLot.prime_location_name) == db.func.lower(new_prime_location_name),
            ParkingLot.id != lot_id
        ).first()
        if existing_lot_with_name:
            flash("A parking lot with this name already exists.", "danger")
            return redirect(url_for("admin_edit_parking_lot", lot_id=lot.id))

        current_spots_count = db.session.query(ParkingSpot).filter_by(lot_id=lot.id).count()

        if new_max_spots < current_spots_count:
            occupied_spots_count = db.session.query(ParkingSpot).filter_by(lot_id=lot.id, status="O").count()
            if new_max_spots < occupied_spots_count:
                flash(f"Cannot reduce spots below {occupied_spots_count} as there are still occupied spots.", "danger")
                return redirect(url_for("admin_edit_parking_lot", lot_id=lot.id))

            # Delete excess spots (start from highest spot_number)
            # Ensure we only delete available spots and in correct order
            spots_to_delete = db.session.query(ParkingSpot).filter_by(
                lot_id=lot.id, status="A"
            ).order_by(ParkingSpot.spot_number.desc()).limit(current_spots_count - new_max_spots).all()

            if len(spots_to_delete) < (current_spots_count - new_max_spots):
                 # This means some spots to be deleted were occupied, so we couldn't get enough available spots
                 # This case should ideally be caught by the occupied_spots_count check above,
                 # but this is a safeguard.
                 flash("Cannot reduce number of spots while there are occupied spots in the ones to be deleted.", "danger")
                 db.session.rollback()
                 return redirect(url_for("admin_edit_parking_lot", lot_id=lot.id))


            for spot in spots_to_delete:
                db.session.delete(spot)

        elif new_max_spots > current_spots_count:
            # Add new spots
            for i in range(current_spots_count + 1, new_max_spots + 1):
                spot = ParkingSpot(lot_id=lot.id, spot_number=i, status="A")
                db.session.add(spot)
        
        lot.prime_location_name = new_prime_location_name
        lot.price_per_hour = price_per_hour
        lot.address = address
        lot.pin_code = pin_code
        lot.maximum_number_of_spots = new_max_spots
        db.session.commit()
        flash("Parking Lot updated successfully!", "success")
        return redirect(url_for("admin_parking_lots"))

    return render_template("admin_edit_parking_lot.html", lot=lot)

@app.route("/admin_delete_parking_lot/<int:lot_id>")
def admin_delete_parking_lot(lot_id):
    if "admin_logged_in" not in session:
        flash("Please login to access the admin dashboard.", "danger")
        return redirect(url_for("admin_login"))

    lot = db.session.query(ParkingLot).get_or_404(lot_id)
    
    occupied_spots = db.session.query(ParkingSpot).filter_by(lot_id=lot.id, status="O").first()
    if occupied_spots:
        flash("Cannot delete parking lot as it contains occupied spots.", "danger")
        return redirect(url_for("admin_parking_lots"))

    db.session.delete(lot)
    db.session.commit()
    flash("Parking Lot deleted successfully!", "success")
    return redirect(url_for("admin_parking_lots"))

# Admin - User Management
@app.route("/admin_users")
def admin_users():
    if "admin_logged_in" not in session:
        flash("Please login to access the admin dashboard.", "danger")
        return redirect(url_for("admin_login"))
    users = db.session.query(User).filter_by(role="user").all()
    return render_template("admin_users.html", users=users)

# Admin - Summary Charts
@app.route("/admin_summary")
def admin_summary():
    if "admin_logged_in" not in session:
        flash("Please login to access the admin dashboard.", "danger")
        return redirect(url_for("admin_login"))

    total_parking_lots = db.session.query(ParkingLot).count()
    total_parking_spots = db.session.query(ParkingSpot).count()
    occupied_parking_spots = db.session.query(ParkingSpot).filter_by(status="O").count()
    available_parking_spots = total_parking_spots - occupied_parking_spots
    total_users = db.session.query(User).filter_by(role="user").count()
    total_reserved_spots = db.session.query(ReservedSpot).count()

    total_revenue = db.session.query(db.func.sum(ReservedSpot.total_cost)).filter(ReservedSpot.total_cost.isnot(None)).scalar() or 0.0

    # Data for charts (using dummy for now, will integrate Chart.js if needed later)
    lot_occupancy_data = []
    parking_lots = db.session.query(ParkingLot).all()
    for lot in parking_lots:
        occupied = db.session.query(ParkingSpot).filter_by(lot_id=lot.id, status="O").count()
        total = db.session.query(ParkingSpot).filter_by(lot_id=lot.id).count()
        lot_occupancy_data.append({'name': lot.prime_location_name, 'occupied': occupied, 'total': total})

    return render_template("admin_summary.html", 
                           total_parking_lots=total_parking_lots,
                           total_parking_spots=total_parking_spots,
                           occupied_parking_spots=occupied_parking_spots,
                           available_parking_spots=available_parking_spots,
                           total_users=total_users,
                           total_reserved_spots=total_reserved_spots,
                           total_revenue=total_revenue,
                           lot_occupancy_data=lot_occupancy_data
                           )

# User - Parking Functionality
@app.route("/book_parking_spot/<int:lot_id>", methods=["GET", "POST"])
def book_parking_spot(lot_id):
    if "user_logged_in" not in session:
        flash("Please login to book a parking spot.", "danger")
        return redirect(url_for("user_login"))

    parking_lot = db.session.query(ParkingLot).get_or_404(lot_id)
    
    if request.method == "POST":
        vehicle_number = request.form["vehicle_number"].strip().upper()
        user_id = session["user_id"]

        if not vehicle_number:
            flash("Vehicle number is required.", "danger")
            return redirect(url_for("book_parking_spot", lot_id=lot_id))

        # Find the first available spot in the selected lot
        available_spot = db.session.query(ParkingSpot).filter_by(lot_id=lot_id, status="A").order_by(ParkingSpot.spot_number).first()

        if not available_spot:
            flash("No available spots in this parking lot.", "danger")
            return redirect(url_for("user_dashboard"))

        # Optional: Check if the user already has an active reservation
        active_reservation = db.session.query(ReservedSpot).filter_by(user_id=user_id, leaving_timestamp=None).first()
        if active_reservation:
            flash("You already have an active parking reservation. Please release it first.", "warning")
            return redirect(url_for("user_dashboard"))

        new_reservation = ReservedSpot(
            spot_id=available_spot.id,
            user_id=user_id,
            vehicle_number=vehicle_number,
            parking_timestamp=datetime.datetime.now()
        )
        db.session.add(new_reservation)
        available_spot.status = "O" # Mark spot as Occupied
        db.session.commit()

        flash(f"Successfully booked spot {available_spot.spot_number} in {parking_lot.prime_location_name}! Vehicle: {vehicle_number}", "success")
        return redirect(url_for("user_dashboard"))

    return render_template("book_parking_spot.html", parking_lot=parking_lot)

@app.route("/release_parking_spot/<int:reservation_id>", methods=["GET", "POST"])
def release_parking_spot(reservation_id):
    if "user_logged_in" not in session:
        flash("Please login to release a parking spot.", "danger")
        return redirect(url_for("user_login"))

    reservation = db.session.query(ReservedSpot).get_or_404(reservation_id)

    # Ensure the reservation belongs to the logged-in user
    if reservation.user_id != session["user_id"]:
        flash("You are not authorized to release this reservation.", "danger")
        return redirect(url_for("user_dashboard"))

    if reservation.leaving_timestamp is not None:
        flash("This spot has already been released.", "warning")
        return redirect(url_for("user_history"))

    parking_spot = db.session.query(ParkingSpot).get_or_404(reservation.spot_id)
    parking_lot = db.session.query(ParkingLot).get_or_404(parking_spot.lot_id)

    if request.method == "POST":
        reservation.leaving_timestamp = datetime.datetime.now()

        # Calculate parking duration and cost
        duration = reservation.leaving_timestamp - reservation.parking_timestamp
        # Convert duration to hours (can be fractional)
        duration_in_hours = duration.total_seconds() / 3600
        total_cost = duration_in_hours * parking_lot.price_per_hour
        reservation.total_cost = round(total_cost, 2) # Round to 2 decimal places

        parking_spot.status = "A" # Mark spot as Available
        db.session.commit()

        flash(f"Spot {parking_spot.spot_number} released successfully! Total cost: ${reservation.total_cost:.2f}", "success")
        return redirect(url_for("user_history"))

    return render_template("release_parking_spot.html", reservation=reservation, parking_spot=parking_spot, parking_lot=parking_lot)

@app.route("/user_history")
def user_history():
    if "user_logged_in" not in session:
        flash("Please login to view your parking history.", "danger")
        return redirect(url_for("user_login"))

    user_id = session["user_id"]
    parking_history = db.session.query(ReservedSpot).filter_by(user_id=user_id).order_by(ReservedSpot.parking_timestamp.desc()).all()

    # Prepare data for rendering, including lot and spot details
    history_data = []
    for res in parking_history:
        spot = db.session.query(ParkingSpot).get(res.spot_id)
        lot = db.session.query(ParkingLot).get(spot.lot_id) if spot else None
        history_data.append({
            'reservation': res,
            'spot': spot,
            'lot': lot
        })

    return render_template("user_history.html", history_data=history_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False) 