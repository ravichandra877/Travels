from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, math, requests
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
DB_PATH = os.path.join(os.path.dirname(__file__), "hanuman_travels.db")
NOMINATIM = "https://nominatim.openstreetmap.org/search"
OSRM = "https://router.project-osrm.org/route/v1/driving"

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','customer'))
        );
        CREATE TABLE IF NOT EXISTS transports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            vehicle_type TEXT NOT NULL,
            capacity TEXT NOT NULL,
            base_location TEXT NOT NULL,
            rate_per_km REAL NOT NULL,
            description TEXT DEFAULT '',
            active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            transport_id INTEGER NOT NULL,
            start_location TEXT NOT NULL,
            destination TEXT NOT NULL,
            distance_km REAL NOT NULL,
            estimated_cost REAL NOT NULL,
            travel_date TEXT NOT NULL,
            passengers INTEGER NOT NULL,
            notes TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES users(id),
            FOREIGN KEY(transport_id) REFERENCES transports(id)
        );
        """)
        admin = con.execute("SELECT id FROM users WHERE email=?", ("admin@hanumantravels.com",)).fetchone()
        if not admin:
            con.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                ("Hanuman Admin", "admin@hanumantravels.com",
                 generate_password_hash("Admin@123"), "admin"))
        if con.execute("SELECT COUNT(*) FROM transports").fetchone()[0] == 0:
            con.executemany("""INSERT INTO transports
                (name,vehicle_type,capacity,base_location,rate_per_km,description)
                VALUES(?,?,?,?,?,?)""", [
                ("Swift Dzire", "Sedan", "4 passengers", "Bengaluru", 14, "Comfortable city and outstation travel."),
                ("Innova Crysta", "SUV", "7 passengers", "Bengaluru", 19, "Spacious family and group travel."),
                ("Tempo Traveller", "Tempo Traveller", "12 passengers", "Bengaluru", 25, "Ideal for group trips and tours.")
            ])

def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("You do not have permission to view that page.", "error")
                return redirect(url_for("home"))
            return fn(*args, **kwargs)
        return wrapped
    return decorator

def geocode(place):
    # Accept "latitude, longitude" directly, otherwise use OpenStreetMap Nominatim.
    try:
        parts = [float(x.strip()) for x in place.split(",")]
        if len(parts) == 2 and -90 <= parts[0] <= 90 and -180 <= parts[1] <= 180:
            return parts[0], parts[1]
    except (ValueError, AttributeError):
        pass
    response = requests.get(NOMINATIM, params={"q": place, "format": "json", "limit": 1},
        headers={"User-Agent": "HanumanTravelsStudentProject/1.0"}, timeout=12)
    response.raise_for_status()
    data = response.json()
    if not data:
        raise ValueError(f"Could not find the location: {place}")
    return float(data[0]["lat"]), float(data[0]["lon"])

def route_distance(start, end):
    a = geocode(start)
    b = geocode(end)
    # OSRM expects longitude,latitude. Its public demo server may occasionally be unavailable.
    coords = f"{a[1]},{a[0]};{b[1]},{b[0]}"
    try:
        r = requests.get(f"{OSRM}/{coords}", params={"overview":"false"}, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data.get("code") == "Ok" and data.get("routes"):
            return data["routes"][0]["distance"] / 1000.0
    except requests.RequestException:
        pass
    # Fallback: straight-line distance using the Haversine formula.
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2-lat1, lon2-lon1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371 * 2 * math.asin(math.sqrt(h))

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        if not name or not email or len(password) < 6:
            flash("Enter your name, a valid email and a password of at least 6 characters.", "error")
        else:
            try:
                with db() as con:
                    con.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                        (name,email,generate_password_hash(password),"customer"))
                flash("Account created. Please log in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("That email address is already registered.", "error")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        with db() as con:
            user = con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session.clear()
            session.update(user_id=user["id"], name=user["name"], role=user["role"])
            return redirect(url_for("admin_dashboard" if user["role"]=="admin" else "customer_dashboard"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))

@app.route("/customer")
@login_required("customer")
def customer_dashboard():
    with db() as con:
        transports = con.execute("SELECT * FROM transports WHERE active=1 ORDER BY id DESC").fetchall()
        bookings = con.execute("""SELECT b.*,t.name AS transport_name FROM bookings b
            JOIN transports t ON t.id=b.transport_id WHERE b.customer_id=? ORDER BY b.id DESC""",
            (session["user_id"],)).fetchall()
    return render_template("customer.html", transports=transports, bookings=bookings)

@app.route("/book", methods=["POST"])
@login_required("customer")
def book():
    start = request.form.get("start_location","").strip()
    destination = request.form.get("destination","").strip()
    date = request.form.get("travel_date","")
    try:
        transport_id = int(request.form.get("transport_id",""))
        passengers = int(request.form.get("passengers","1"))
        if not start or not destination or not date or passengers < 1:
            raise ValueError("Please complete all required booking details.")
        with db() as con:
            vehicle = con.execute("SELECT * FROM transports WHERE id=? AND active=1", (transport_id,)).fetchone()
            if not vehicle:
                raise ValueError("Please select an available transport.")
        km = route_distance(start, destination)
        cost = round(km * vehicle["rate_per_km"], 2)
        with db() as con:
            con.execute("""INSERT INTO bookings(customer_id,transport_id,start_location,destination,
                distance_km,estimated_cost,travel_date,passengers,notes)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (session["user_id"],transport_id,start,destination,km,cost,date,passengers,
                 request.form.get("notes","").strip()))
        flash(f"Booking request sent! Estimated distance: {km:.1f} km. Estimated fare: ₹{cost:,.0f}.", "success")
    except (ValueError, requests.RequestException) as e:
        flash(str(e) or "Could not calculate the route. Check your internet connection and locations.", "error")
    except Exception:
        flash("Booking could not be completed. Please check the locations and try again.", "error")
    return redirect(url_for("customer_dashboard"))

@app.route("/admin")
@login_required("admin")
def admin_dashboard():
    with db() as con:
        transports = con.execute("SELECT * FROM transports ORDER BY id DESC").fetchall()
        bookings = con.execute("""SELECT b.*,u.name AS customer_name,u.email,t.name AS transport_name
            FROM bookings b JOIN users u ON u.id=b.customer_id
            JOIN transports t ON t.id=b.transport_id ORDER BY b.id DESC""").fetchall()
    return render_template("admin.html", transports=transports, bookings=bookings)

@app.route("/admin/add-transport", methods=["POST"])
@login_required("admin")
def add_transport():
    try:
        name = request.form["name"].strip()
        vehicle_type = request.form["vehicle_type"].strip()
        capacity = request.form["capacity"].strip()
        location = request.form["base_location"].strip()
        rate = float(request.form["rate_per_km"])
        if not all([name,vehicle_type,capacity,location]) or rate <= 0:
            raise ValueError()
        with db() as con:
            con.execute("""INSERT INTO transports(name,vehicle_type,capacity,base_location,rate_per_km,description)
                VALUES(?,?,?,?,?,?)""", (name,vehicle_type,capacity,location,rate,request.form.get("description","").strip()))
        flash("Transport added successfully.", "success")
    except Exception:
        flash("Please enter valid transport details and a rate greater than zero.", "error")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/booking/<int:booking_id>/<action>", methods=["POST"])
@login_required("admin")
def booking_action(booking_id, action):
    statuses = {"accept":"Accepted", "reject":"Rejected"}
    if action not in statuses:
        flash("Invalid booking action.", "error")
    else:
        with db() as con:
            con.execute("UPDATE bookings SET status=? WHERE id=?", (statuses[action],booking_id))
        flash(f"Booking #{booking_id} marked {statuses[action].lower()}.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/transport/<int:transport_id>/toggle", methods=["POST"])
@login_required("admin")
def toggle_transport(transport_id):
    with db() as con:
        con.execute("UPDATE transports SET active=CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=?", (transport_id,))
    return redirect(url_for("admin_dashboard"))

@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
