from flask import Flask, render_template, request, redirect, url_for, session, flash
import datetime, os
from model import db, User, ParkingLot, ParkingSpot, ReservedSpot

app = Flask(__name__, template_folder="templates")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///parking.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "supersecretkeyforvehicleparkingapp")
db.init_app(app)

# --- DB Init & Admin ---
with app.app_context():
    try:
        db.create_all()

        # If you see two admins, that's on you!
        if not User.query.filter_by(role="admin").first():
            admin = User(email_id="admin@parking.com", password="admin", full_name="Administrator", address="Admin Address", pin_code="000000", role="admin")
            db.session.add(admin)
            db.session.commit()
            print("Admin account created.")
        else:
            print("Admin account already exists.")
        print("Database initialization complete.")
    except Exception as e:
        print("DB setup error:", e)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")
def health_check():
    return {"status": "healthy", "message": "Yep, it's running!"}, 200

@app.route("/user_register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        email = request.form["email_id"]
        pwd = request.form["password"]
        name = request.form["full_name"]
        addr = request.form["address"]
        pin = request.form["pin_code"]
        if User.query.filter_by(email_id=email).first():
            flash("That email is already taken. Try logging in or use a different one.", "danger")
            return redirect(url_for("user_register"))
        user = User(email_id=email, password=pwd, full_name=name, address=addr, pin_code=pin, role="user")
        db.session.add(user)
        db.session.commit()
        flash("All set! Now log in and grab a spot.", "success")
        return redirect(url_for("user_login"))
    return render_template("user_register.html")

@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        email = request.form["email_id"]
        pwd = request.form["password"]
        user = User.query.filter_by(email_id=email, role="user").first()
        if user and user.password == pwd:
            session.clear()
            session["user_logged_in"] = True
            session["user_id"] = user.id
            session["user_email"] = user.email_id
            flash(f"Hey {user.full_name}, you made it!", "success")
            return redirect(url_for("user_dashboard"))
        flash("Nope, that's not right. Try again!", "danger")
        return redirect(url_for("user_login"))
    return render_template("user_login.html")

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email_id"]
        pwd = request.form["password"]
        admin = User.query.filter_by(email_id=email, role="admin").first()
        if admin and admin.password == pwd:
            session.clear()
            session["admin_logged_in"] = True
            session["admin_id"] = admin.id
            flash("Welcome back, boss!", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Nope, that's not the admin login.", "danger")
        return redirect(url_for("admin_login"))
    return render_template("admin_login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out. See you next time!", "info")
    return redirect(url_for("home"))

@app.route("/user_dashboard")
def user_dashboard():
    if "user_logged_in" not in session:
        flash("Please log in to see your dashboard.", "danger")
        return redirect(url_for("user_login"))
    search = request.args.get('query', '').strip()
    lots = db.session.query(ParkingLot).all()
    data = []
    for lot in lots:
        total = db.session.query(ParkingSpot).filter_by(lot_id=lot.id).count()
        available = db.session.query(ParkingSpot).filter_by(lot_id=lot.id, status="A").count()
        if not search or search.lower() in lot.prime_location_name.lower() or search.lower() in lot.address.lower() or search.lower() in lot.pin_code.lower():
            data.append({'lot': lot, 'total_spots': total, 'available_spots': available})
    data.sort(key=lambda x: x['lot'].prime_location_name.lower())
    user_id = session.get("user_id")
    chart = []
    if user_id:
        monthly = db.session.query(
            db.func.strftime('%Y-%m', ReservedSpot.parking_timestamp).label('month'),
            db.func.sum(ReservedSpot.total_cost).label('total_cost')
        ).filter(
            ReservedSpot.user_id == user_id, ReservedSpot.total_cost.isnot(None)
        ).group_by('month').order_by('month').all()
        for item in monthly:
            chart.append({'month': item.month, 'total_cost': item.total_cost})
    return render_template("user_dashboard.html", parking_lots_data=data, parking_data_for_chart=chart, query=search)

@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin_logged_in" not in session:
        flash("Please log in to see the admin dashboard.", "danger")
        return redirect(url_for("admin_login"))
    return render_template("admin_dashboard.html")

@app.route("/admin_parking_lots", methods=["GET", "POST"])
def admin_parking_lots():
    if "admin_logged_in" not in session:
        flash("Please log in to see the admin dashboard.", "danger")
        return redirect(url_for("admin_login"))
    if request.method == "POST":
        name = request.form["prime_location_name"].strip()
        rate = float(request.form["price_per_hour"])
        addr = request.form["address"].strip()
        pin = request.form["pin_code"].strip()
        max_spots = int(request.form["maximum_number_of_spots"])
        if not name or not addr or not pin:
            flash("Fill out all the fields, please.", "danger")
            return redirect(url_for("admin_parking_lots"))
        if rate <= 0:
            flash("Hourly rate must be positive. No free parking here!", "danger")
            return redirect(url_for("admin_parking_lots"))
        if max_spots < 1:
            flash("There must be at least one spot. Otherwise, what's the point?", "danger")
            return redirect(url_for("admin_parking_lots"))
        if db.session.query(ParkingLot).filter(db.func.lower(ParkingLot.prime_location_name) == db.func.lower(name)).first():
            flash("A parking lot with this name already exists. Try another name.", "danger")
            return redirect(url_for("admin_parking_lots"))
        lot = ParkingLot(prime_location_name=name, price_per_hour=rate, address=addr, pin_code=pin, maximum_number_of_spots=max_spots)
        db.session.add(lot)
        db.session.commit()
        for i in range(1, max_spots + 1):
            spot = ParkingSpot(lot_id=lot.id, spot_number=i, status="A")
            db.session.add(spot)
        db.session.commit()
        flash("Parking lot added!", "success")
        return redirect(url_for("admin_parking_lots"))
    lots = db.session.query(ParkingLot).order_by(ParkingLot.prime_location_name).all()
    lot_data = []
    for lot in lots:
        total = db.session.query(ParkingSpot).filter_by(lot_id=lot.id).count()
        occupied = db.session.query(ParkingSpot).filter_by(lot_id=lot.id, status="O").count()
        spots = db.session.query(ParkingSpot).filter_by(lot_id=lot.id).order_by(ParkingSpot.spot_number).all()
        lot_data.append({'lot': lot, 'total_spots': total, 'occupied_spots': occupied, 'spots_list': spots})
    return render_template("admin_parking_lots.html", lot_data=lot_data)

@app.route("/admin_edit_parking_lot/<int:lot_id>", methods=["GET", "POST"])
def admin_edit_parking_lot(lot_id):
    if "admin_logged_in" not in session:
        flash("Please log in to see the admin dashboard.", "danger")
        return redirect(url_for("admin_login"))
    lot = db.session.query(ParkingLot).get_or_404(lot_id)
    if request.method == "POST":
        name = request.form["prime_location_name"].strip()
        rate = float(request.form["price_per_hour"])
        addr = request.form["address"].strip()
        pin = request.form["pin_code"].strip()
        max_spots = int(request.form["maximum_number_of_spots"])
        if not name or not addr or not pin:
            flash("Don't leave anything blank!", "danger")
            return redirect(url_for("admin_edit_parking_lot", lot_id=lot.id))
        if rate <= 0:
            flash("Hourly rate must be positive. No free parking!", "danger")
            return redirect(url_for("admin_edit_parking_lot", lot_id=lot.id))
        if max_spots < 1:
            flash("There must be at least one spot.", "danger")
            return redirect(url_for("admin_edit_parking_lot", lot_id=lot.id))
        if db.session.query(ParkingLot).filter(db.func.lower(ParkingLot.prime_location_name) == db.func.lower(name), ParkingLot.id != lot_id).first():
            flash("A parking lot with this name already exists.", "danger")
            return redirect(url_for("admin_edit_parking_lot", lot_id=lot.id))
        current_spots = db.session.query(ParkingSpot).filter_by(lot_id=lot.id).count()
        if max_spots < current_spots:
            occupied = db.session.query(ParkingSpot).filter_by(lot_id=lot.id, status="O").count()
            if max_spots < occupied:
                flash(f"Can't reduce spots below {occupied} because some are still occupied.", "danger")
                return redirect(url_for("admin_edit_parking_lot", lot_id=lot.id))
            spots_to_delete = db.session.query(ParkingSpot).filter_by(lot_id=lot.id, status="A").order_by(ParkingSpot.spot_number.desc()).limit(current_spots - max_spots).all()
            if len(spots_to_delete) < (current_spots - max_spots):
                flash("Can't reduce spots while some of the ones to be deleted are occupied.", "danger")
                db.session.rollback()
                return redirect(url_for("admin_edit_parking_lot", lot_id=lot.id))
            for spot in spots_to_delete:
                db.session.delete(spot)
        elif max_spots > current_spots:
            for i in range(current_spots + 1, max_spots + 1):
                spot = ParkingSpot(lot_id=lot.id, spot_number=i, status="A")
                db.session.add(spot)
        lot.prime_location_name = name
        lot.price_per_hour = rate
        lot.address = addr
        lot.pin_code = pin
        lot.maximum_number_of_spots = max_spots
        db.session.commit()
        flash("Parking lot updated!", "success")
        return redirect(url_for("admin_parking_lots"))
    return render_template("admin_edit_parking_lot.html", lot=lot)

@app.route("/admin_delete_parking_lot/<int:lot_id>")
def admin_delete_parking_lot(lot_id):
    if "admin_logged_in" not in session:
        flash("Please log in to see the admin dashboard.", "danger")
        return redirect(url_for("admin_login"))
    lot = db.session.query(ParkingLot).get_or_404(lot_id)
    if db.session.query(ParkingSpot).filter_by(lot_id=lot.id, status="O").first():
        flash("Can't delete this parking lot because it has occupied spots.", "danger")
        return redirect(url_for("admin_parking_lots"))
    db.session.delete(lot)
    db.session.commit()
    flash("Parking lot deleted!", "success")
    return redirect(url_for("admin_parking_lots"))

@app.route("/admin_users")
def admin_users():
    if "admin_logged_in" not in session:
        flash("Please log in to see the admin dashboard.", "danger")
        return redirect(url_for("admin_login"))
    users = db.session.query(User).filter_by(role="user").all()
    return render_template("admin_users.html", users=users)

@app.route("/admin_summary")
def admin_summary():
    if "admin_logged_in" not in session:
        flash("Please log in to see the admin dashboard.", "danger")
        return redirect(url_for("admin_login"))
    total_lots = db.session.query(ParkingLot).count()
    total_spots = db.session.query(ParkingSpot).count()
    occupied_spots = db.session.query(ParkingSpot).filter_by(status="O").count()
    available_spots = total_spots - occupied_spots
    total_users = db.session.query(User).filter_by(role="user").count()
    total_reserved_spots = db.session.query(ReservedSpot).count()
    total_revenue = db.session.query(db.func.sum(ReservedSpot.total_cost)).filter(ReservedSpot.total_cost.isnot(None)).scalar() or 0.0
    lot_occupancy = []
    lots = db.session.query(ParkingLot).all()
    for lot in lots:
        occupied = db.session.query(ParkingSpot).filter_by(lot_id=lot.id, status="O").count()
        total = db.session.query(ParkingSpot).filter_by(lot_id=lot.id).count()
        lot_occupancy.append({'name': lot.prime_location_name, 'occupied': occupied, 'total': total})
    return render_template("admin_summary.html", total_parking_lots=total_lots, total_parking_spots=total_spots, occupied_parking_spots=occupied_spots, available_parking_spots=available_spots, total_users=total_users, total_reserved_spots=total_reserved_spots, total_revenue=total_revenue, lot_occupancy_data=lot_occupancy)

@app.route("/book_parking_spot/<int:lot_id>", methods=["GET", "POST"])
def book_parking_spot(lot_id):
    if "user_logged_in" not in session:
        flash("Please log in to book a parking spot.", "danger")
        return redirect(url_for("user_login"))
    parking_lot = db.session.query(ParkingLot).get_or_404(lot_id)
    if request.method == "POST":
        vehicle_number = request.form["vehicle_number"].strip().upper()
        user_id = session["user_id"]
        if not vehicle_number:
            flash("Don't forget your vehicle number!", "danger")
            return redirect(url_for("book_parking_spot", lot_id=lot_id))
        available_spot = db.session.query(ParkingSpot).filter_by(lot_id=lot_id, status="A").order_by(ParkingSpot.spot_number).first()
        if not available_spot:
            flash("No spots left in this lot. Try another one!", "danger")
            return redirect(url_for("user_dashboard"))
        active_reservation = db.session.query(ReservedSpot).filter_by(user_id=user_id, leaving_timestamp=None).first()
        if active_reservation:
            flash("You already have a spot. Release it before booking again!", "warning")
            return redirect(url_for("user_dashboard"))
        new_reservation = ReservedSpot(spot_id=available_spot.id, user_id=user_id, vehicle_number=vehicle_number, parking_timestamp=datetime.datetime.now())
        db.session.add(new_reservation)
        available_spot.status = "O"
        db.session.commit()
        flash(f"Spot {available_spot.spot_number} in {parking_lot.prime_location_name} is yours! Vehicle: {vehicle_number}", "success")
        return redirect(url_for("user_dashboard"))
    return render_template("book_parking_spot.html", parking_lot=parking_lot)

@app.route("/release_parking_spot/<int:reservation_id>", methods=["GET", "POST"])
def release_parking_spot(reservation_id):
    if "user_logged_in" not in session:
        flash("Please log in to release your parking spot.", "danger")
        return redirect(url_for("user_login"))
    reservation = db.session.query(ReservedSpot).get_or_404(reservation_id)
    if reservation.user_id != session["user_id"]:
        flash("Nice try, but that's not your reservation!", "danger")
        return redirect(url_for("user_dashboard"))
    if reservation.leaving_timestamp is not None:
        flash("This spot is already released.", "warning")
        return redirect(url_for("user_history"))
    parking_spot = db.session.query(ParkingSpot).get_or_404(reservation.spot_id)
    parking_lot = db.session.query(ParkingLot).get_or_404(parking_spot.lot_id)
    if request.method == "POST":
        reservation.leaving_timestamp = datetime.datetime.now()
        duration = reservation.leaving_timestamp - reservation.parking_timestamp
        hours = duration.total_seconds() / 3600
        total_cost = hours * parking_lot.price_per_hour
        reservation.total_cost = round(total_cost, 2)
        parking_spot.status = "A"
        db.session.commit()
        flash(f"Spot {parking_spot.spot_number} released! You owe: ${reservation.total_cost:.2f}", "success")
        return redirect(url_for("user_history"))
    return render_template("release_parking_spot.html", reservation=reservation, parking_spot=parking_spot, parking_lot=parking_lot)

@app.route("/user_history")
def user_history():
    if "user_logged_in" not in session:
        flash("Please log in to see your parking history.", "danger")
        return redirect(url_for("user_login"))
    user_id = session["user_id"]
    history = db.session.query(ReservedSpot).filter_by(user_id=user_id).order_by(ReservedSpot.parking_timestamp.desc()).all()
    history_data = []
    for res in history:
        spot = db.session.query(ParkingSpot).get(res.spot_id)
        lot = db.session.query(ParkingLot).get(spot.lot_id) if spot else None
        history_data.append({'reservation': res, 'spot': spot, 'lot': lot})
    return render_template("user_history.html", history_data=history_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False) 