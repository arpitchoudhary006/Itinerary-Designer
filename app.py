"""
HIMALAYAN TRAVEL ITINERARY DESIGNER
Complete Production-Ready Flask Web Application
Features:
- Authentication & User Ownership Security
- High-Altitude Weather Forecasts (Live Open-Meteo & Advisory Engine)
- Verified Nearby Hotels, Homestays & Eco Camps with Direct Host Contact
- Interactive Leaflet Maps with Topographic Terrain & Custom Pins
- Multi-Day Itinerary Generator, Customizer & TXT Exporter
- Default Start with Welcoming Himalayan Login Experience
"""

import os
import secrets
import sqlite3
import uuid
from ast import literal_eval
from datetime import datetime, date, timedelta, timezone
from io import BytesIO
from typing import Dict, List, Optional
from urllib.parse import urlsplit

from flask import (
    Flask,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    send_file,
    url_for,
    jsonify,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models import User, get_db, init_db, now_iso, row_to_dict
from services.data_presets import DESTINATION_PRESETS
from services.weather_service import fetch_weather_forecast

# Initialize Flask App
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please sign in to access your itineraries and saved Himalayan plans."
login_manager.login_message_category = "info"

TRAVEL_STYLES = ["Budget", "Moderate", "Luxury"]
TRANSPORT_OPTIONS = ["Flight", "Train", "Bus", "Car"]
ACCOMMODATION_OPTIONS = ["Homestay", "Eco Camp / Tent", "Hostel", "Budget Hotel", "3-Star Hotel", "4-Star Hotel", "5-Star Resort"]
PREFERENCE_BUDGETS = ["Flexible", "Under INR 15,000", "INR 15,000-40,000", "Over INR 40,000"]


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return User(row) if row else None
    finally:
        db.close()


def create_user(name, email, password, role="USER"):
    db = get_db()
    try:
        normalized_email = email.lower().strip()
        if db.execute("SELECT id FROM users WHERE email = ?", (normalized_email,)).fetchone():
            return None, "Email address is already registered."
        user_id = f"usr_{uuid.uuid4().hex[:10]}"
        now = now_iso()
        db.execute(
            """INSERT INTO users (user_id, organization_id, name, email, password_hash, role, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, "org_default", name.strip(), normalized_email, generate_password_hash(password), role, now, now),
        )
        db.commit()
        user_row = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return User(user_row), None
    except sqlite3.IntegrityError:
        db.rollback()
        return None, "Email address is already registered."
    finally:
        db.close()


def seed_database():
    """Seeds destinations, hotels, homestays, activities, templates, and demo accounts."""
    init_db()
    db = get_db()
    now = now_iso()
    try:
        # 1. Seed or Update Admin Account (arpit.06)
        admin_username = Config.ADMIN_USERNAME.strip()
        admin_email = Config.ADMIN_EMAIL.lower().strip()
        admin_password = Config.ADMIN_PASSWORD
        admin_name = Config.ADMIN_NAME

        # Clean up legacy demo accounts
        db.execute("DELETE FROM users WHERE user_id IN ('usr_demo_traveler', 'usr_demo_admin') OR email IN ('traveler@himalayas.com', 'admin@himalayas.com')")

        existing_admin = db.execute(
            "SELECT id, user_id FROM users WHERE LOWER(name) = ? OR LOWER(email) = ? OR user_id = 'usr_arpit06'",
            (admin_username.lower(), admin_email),
        ).fetchone()

        if not existing_admin:
            db.execute(
                """INSERT INTO users (user_id, organization_id, name, email, password_hash, role, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "usr_arpit06",
                    "org_default",
                    admin_name,
                    admin_email,
                    generate_password_hash(admin_password),
                    "ADMIN",
                    now,
                    now,
                ),
            )
            admin_uid = "usr_arpit06"
        else:
            admin_uid = existing_admin["user_id"]
            db.execute(
                """UPDATE users SET name = ?, email = ?, password_hash = ?, role = 'ADMIN', updated_at = ? WHERE id = ?""",
                (admin_name, admin_email, generate_password_hash(admin_password), now, existing_admin["id"]),
            )

        # 3. Seed Destinations, Hotels, Homestays, Activities, and Templates
        for slug, data in DESTINATION_PRESETS.items():
            existing = db.execute("SELECT id FROM destinations WHERE slug = ?", (slug,)).fetchone()
            if existing:
                dest_id = existing["id"]
            else:
                cur = db.execute(
                    """INSERT INTO destinations (name, slug, state, description, duration, difficulty,
                                                elevation, best_time, estimated_budget, latitude, longitude,
                                                organization_id, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        data["name"],
                        slug,
                        data["state"],
                        data["description"],
                        data["duration"],
                        data["difficulty"],
                        data["elevation"],
                        data["best_time"],
                        data["estimated_budget"],
                        data["latitude"],
                        data["longitude"],
                        "org_default",
                        now,
                        now,
                    ),
                )
                dest_id = cur.lastrowid

            # Destination Images
            for idx, img_url in enumerate(data.get("images", [])):
                if not db.execute("SELECT id FROM destination_images WHERE destination_id = ? AND image_url = ?", (dest_id, img_url)).fetchone():
                    db.execute(
                        """INSERT INTO destination_images (destination_id, image_url, caption, is_primary, created_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (dest_id, img_url, f"{data['name']} view {idx + 1}", 1 if idx == 0 else 0, now),
                    )

            # Destination Accommodations (Hotels, Homestays & Eco Camps)
            for acc in data.get("accommodations", []):
                if not db.execute("SELECT id FROM accommodations WHERE destination_id = ? AND name = ?", (dest_id, acc["name"])).fetchone():
                    db.execute(
                        """INSERT INTO accommodations (destination_id, name, type, price_per_night, rating, reviews_count,
                                                      distance, amenities, phone, booking_url, description, image_url,
                                                      latitude, longitude, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            dest_id,
                            acc["name"],
                            acc["type"],
                            acc["price_per_night"],
                            acc["rating"],
                            acc.get("reviews_count", 50),
                            acc.get("distance", ""),
                            acc.get("amenities", ""),
                            acc.get("phone", ""),
                            acc.get("booking_url", ""),
                            acc.get("description", ""),
                            acc.get("image_url", ""),
                            acc.get("latitude", data["latitude"]),
                            acc.get("longitude", data["longitude"]),
                            now,
                        ),
                    )

            # Destination Activities
            for act in data.get("activities", []):
                act_name = act["name"] if isinstance(act, dict) else act
                if not db.execute("SELECT id FROM activities WHERE destination_id = ? AND name = ?", (dest_id, act_name)).fetchone():
                    desc = act.get("description", f"Experience {act_name} in {data['name']}.") if isinstance(act, dict) else f"{act_name} activity in {data['name']}."
                    duration = act.get("duration", "2-3 hrs") if isinstance(act, dict) else "2-3 hrs"
                    cost = act.get("cost", 300) if isinstance(act, dict) else 300
                    lat = act.get("lat", data["latitude"]) if isinstance(act, dict) else data["latitude"]
                    lng = act.get("lng", data["longitude"]) if isinstance(act, dict) else data["longitude"]
                    db.execute(
                        """INSERT INTO activities (destination_id, name, description, duration, estimated_cost,
                                                   difficulty, category, image_url, latitude, longitude, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (dest_id, act_name, desc, duration, cost, data["difficulty"], "general", data["images"][0] if data["images"] else "", lat, lng, now, now),
                    )

            # Destination Templates
            if not db.execute("SELECT id FROM itinerary_templates WHERE destination_id = ?", (dest_id,)).fetchone():
                template_json = {"destination": data["name"], "days": data.get("template", [])}
                db.execute(
                    """INSERT INTO itinerary_templates (destination_id, name, day_count, template_data, estimated_budget, last_updated)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (dest_id, f"{data['name']} Suggested Plan", len(data.get("template", [])), str(template_json), data["estimated_budget"], now),
                )

        # 4. Seed an initial sample itinerary for the admin if none exists
        db.execute("UPDATE itineraries SET owner_id = ? WHERE owner_id = 'usr_demo_traveler'", (admin_uid,))
        if not db.execute("SELECT id FROM itineraries WHERE owner_id = ?", (admin_uid,)).fetchone():
            chopta = db.execute("SELECT id, estimated_budget FROM destinations WHERE slug = 'tungnath-chandrashila'").fetchone()
            homestay = db.execute("SELECT id FROM accommodations WHERE destination_id = ? AND type = 'Homestay' LIMIT 1", (chopta["id"],)).fetchone() if chopta else None
            if chopta:
                start_d = (date.today() + timedelta(days=7)).isoformat()
                end_d = (date.today() + timedelta(days=10)).isoformat()
                cur = db.execute(
                    """INSERT INTO itineraries (owner_id, name, destination_id, accommodation_id, start_date, end_date,
                                               number_of_travelers, travel_style, transport_preference, accommodation_preference,
                                               budget, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        admin_uid,
                        "Autumn Chandrashila Summit & Tungnath Trek",
                        chopta["id"],
                        homestay["id"] if homestay else None,
                        start_d,
                        end_d,
                        2,
                        "Moderate",
                        "Train",
                        "Homestay",
                        15000.0,
                        now,
                        now,
                    ),
                )
                itin_id = cur.lastrowid
                # Add Days
                t_data = DESTINATION_PRESETS["tungnath-chandrashila"]["template"]
                for idx, d_info in enumerate(t_data, 1):
                    day_d = (date.today() + timedelta(days=6 + idx)).isoformat()
                    d_cur = db.execute(
                        """INSERT INTO itinerary_days (itinerary_id, day_number, date, title, notes)
                           VALUES (?, ?, ?, ?, ?)""",
                        (itin_id, idx, day_d, d_info["title"], d_info["notes"]),
                    )
                    day_id = d_cur.lastrowid
                    for order, act_item in enumerate(d_info.get("activities", [])):
                        db.execute(
                            """INSERT INTO itinerary_activities (itinerary_day_id, custom_name, start_time, duration,
                                                               estimated_cost, notes, display_order)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (day_id, act_item["name"], act_item["time"], act_item["duration"], act_item["cost"], "Scheduled activity", order),
                        )

        db.commit()
    finally:
        db.close()


def safe_redirect_target(target):
    if not target:
        return None
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or not target.startswith("/"):
        return None
    return target


def get_destination_by_slug(slug: str):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM destinations WHERE slug = ?", (slug,)).fetchone()
        return row_to_dict(row)
    finally:
        db.close()


def list_destinations(search=""):
    db = get_db()
    try:
        query = """
            SELECT d.*,
                   (SELECT image_url FROM destination_images
                    WHERE destination_id = d.id ORDER BY is_primary DESC, id ASC LIMIT 1) AS image_url
            FROM destinations d
        """
        params = ()
        if search:
            pat = f"%{search}%"
            query += " WHERE d.name LIKE ? OR d.state LIKE ? OR d.description LIKE ?"
            params = (pat, pat, pat)
        query += " ORDER BY d.name"
        return [dict(r) for r in db.execute(query, params).fetchall()]
    finally:
        db.close()


def get_accommodations(destination_id: int):
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM accommodations WHERE destination_id = ? ORDER BY rating DESC, price_per_night ASC",
            (destination_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


def get_destination_activities(destination_id: int):
    db = get_db()
    try:
        rows = db.execute("SELECT * FROM activities WHERE destination_id = ? ORDER BY id ASC", (destination_id,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


def get_destination_images(destination_id: int):
    db = get_db()
    try:
        rows = db.execute("SELECT * FROM destination_images WHERE destination_id = ? ORDER BY is_primary DESC, id ASC", (destination_id,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


def fetch_reviews(destination_id: int):
    db = get_db()
    try:
        rows = db.execute(
            """SELECT r.*, u.name FROM reviews r
               LEFT JOIN users u ON u.user_id = r.owner_id
               WHERE r.destination_id = ? ORDER BY r.created_at DESC""",
            (destination_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


def get_owned_itinerary_or_404(itinerary_id: int):
    db = get_db()
    try:
        row = db.execute(
            "SELECT * FROM itineraries WHERE id = ? AND owner_id = ?",
            (itinerary_id, current_user.user_id),
        ).fetchone()
        if not row:
            abort(404)
        return dict(row)
    finally:
        db.close()


def get_itinerary_detail(itinerary_id: int):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM itineraries WHERE id = ?", (itinerary_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        
        # Destination
        if data.get("destination_id"):
            dest_row = db.execute("SELECT * FROM destinations WHERE id = ?", (data["destination_id"],)).fetchone()
            data["destination"] = dict(dest_row) if dest_row else None
        else:
            data["destination"] = None
            
        # Accommodation
        if data.get("accommodation_id"):
            acc_row = db.execute("SELECT * FROM accommodations WHERE id = ?", (data["accommodation_id"],)).fetchone()
            data["accommodation"] = dict(acc_row) if acc_row else None
        else:
            data["accommodation"] = None

        # Days & Activities
        days = db.execute("SELECT * FROM itinerary_days WHERE itinerary_id = ? ORDER BY day_number ASC", (itinerary_id,)).fetchall()
        data["days"] = []
        for day in days:
            d = dict(day)
            acts = db.execute(
                """SELECT ia.*, a.name AS activity_name FROM itinerary_activities ia
                   LEFT JOIN activities a ON a.id = ia.activity_id
                   WHERE ia.itinerary_day_id = ? ORDER BY ia.display_order ASC, ia.id ASC""",
                (day["id"],),
            ).fetchall()
            d["activities"] = [dict(a) for a in acts]
            data["days"].append(d)

        return data
    finally:
        db.close()


def get_user_preferences(owner_id: str):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM travel_preferences WHERE owner_id = ? ORDER BY id DESC LIMIT 1", (owner_id,)).fetchone()
        return dict(row) if row else {}
    finally:
        db.close()


def get_saved_destinations(owner_id: str):
    db = get_db()
    try:
        rows = db.execute(
            """SELECT s.*, d.name, d.slug, d.state FROM saved_destinations s
               LEFT JOIN destinations d ON d.id = s.destination_id
               WHERE s.owner_id = ? ORDER BY s.created_at DESC""",
            (owner_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


def write_itinerary_schedule(db, itinerary_id, trip, existing_days=None, form=None):
    existing_days = existing_days or []
    start = date.fromisoformat(trip["start_date"])
    preset = DESTINATION_PRESETS.get(trip["destination"]["slug"], {})
    template_days = preset.get("template", [])

    old_activity_details = {
        day["day_number"]: {
            (activity.get("custom_name") or activity.get("activity_name") or ""): activity
            for activity in day.get("activities", [])
        }
        for day in existing_days
    }

    db.execute(
        "DELETE FROM itinerary_activities WHERE itinerary_day_id IN (SELECT id FROM itinerary_days WHERE itinerary_id = ?)",
        (itinerary_id,),
    )
    db.execute("DELETE FROM itinerary_days WHERE itinerary_id = ?", (itinerary_id,))

    for offset in range(trip["days"]):
        day_number = offset + 1
        defaults = template_days[offset % len(template_days)] if template_days else {
            "title": f"Day {day_number}",
            "notes": "Acclimatize, trek, and explore local culture.",
            "activities": [],
        }
        previous = existing_days[offset] if offset < len(existing_days) else None

        title = form.get(f"day_title_{day_number}", "").strip() if form and previous else ""
        notes = form.get(f"day_notes_{day_number}", "").strip() if form and previous else ""
        title = title or (previous["title"] if previous else defaults.get("title", f"Day {day_number}"))
        notes = notes if form and previous else (previous["notes"] if previous else defaults.get("notes", ""))

        old_activities = old_activity_details.get(day_number, {})
        if form and previous:
            activity_names = [line.strip() for line in form.get(f"day_activities_{day_number}", "").splitlines() if line.strip()]
        elif previous:
            activity_names = list(old_activities)
        else:
            activity_names = [act.get("name", "") for act in defaults.get("activities", []) if act.get("name")]

        day_date = start + timedelta(days=offset)
        cur = db.execute(
            "INSERT INTO itinerary_days (itinerary_id, day_number, date, title, notes) VALUES (?, ?, ?, ?, ?)",
            (itinerary_id, day_number, day_date.isoformat(), title, notes),
        )
        day_id = cur.lastrowid

        for order, act_name in enumerate(activity_names):
            old_act = old_activities.get(act_name, {})
            t_act = next((item for item in defaults.get("activities", []) if item.get("name") == act_name), {})
            db.execute(
                """INSERT INTO itinerary_activities (itinerary_day_id, custom_name, start_time, duration,
                                                     estimated_cost, notes, display_order)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    day_id,
                    act_name,
                    old_act.get("start_time") or t_act.get("time", ""),
                    old_act.get("duration") or t_act.get("duration", ""),
                    float(old_act.get("estimated_cost") or t_act.get("cost") or 0),
                    old_act.get("notes", "Planned stop"),
                    order,
                ),
            )


# ==============================================================================
# BEFORE REQUEST HOOKS (INIT & CSRF PROTECTION)
# ==============================================================================
@app.before_request
def prepare_request():
    init_key = f"himalayan_app_init:{os.path.abspath(Config.DB_PATH)}"
    if not app.extensions.get(init_key):
        seed_database()
        app.extensions[init_key] = True

    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)

    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        submitted = request.form.get("csrf_token", "")
        if not secrets.compare_digest(session.get("_csrf_token", ""), submitted):
            abort(400)


@app.context_processor
def inject_context():
    return {
        "csrf_token": session.get("_csrf_token", ""),
        "now_year": datetime.now().year,
    }


# ==============================================================================
# APPLICATION ROUTES
# ==============================================================================

# 1. ROOT LANDING PAGE: START DIRECTLY WITH LOGIN (As explicitly requested)
@app.route("/")
def home():
    if not current_user.is_authenticated:
        # User requested: "and start this website with login page"
        return redirect(url_for("login"))
    return redirect(url_for("dashboard"))


# 2. AUTHENTICATION: LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        login_identifier = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        try:
            row = db.execute(
                "SELECT * FROM users WHERE LOWER(email) = LOWER(?) OR LOWER(name) = LOWER(?) OR LOWER(user_id) = LOWER(?)",
                (login_identifier, login_identifier, login_identifier),
            ).fetchone()
        finally:
            db.close()

        if row and check_password_hash(row["password_hash"], password):
            session["_csrf_token"] = secrets.token_urlsafe(32)
            login_user(User(row))
            session.permanent = True
            flash(f"Welcome back to the Himalayas, {row['name']}!", "success")
            next_url = safe_redirect_target(request.form.get("next") or request.args.get("next"))
            return redirect(next_url or url_for("dashboard"))
        error = "Invalid username/email or password."

    next_url = safe_redirect_target(request.args.get("next")) or ""
    return render_template("login.html", error=error, next_url=next_url)


# 3. AUTHENTICATION: REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirmation = request.form.get("password_confirmation", "")

        if not 2 <= len(name) <= 80:
            error = "Name must be between 2 and 80 characters."
        elif len(email) > 254 or "@" not in email or any(c.isspace() for c in email):
            error = "Enter a valid email address."
        elif len(password) < 10 or len(password) > 128:
            error = "Password must be at least 10 characters long."
        elif password != confirmation:
            error = "Passwords do not match."
        else:
            user, error = create_user(name, email, password)
            if user:
                session["_csrf_token"] = secrets.token_urlsafe(32)
                login_user(user)
                session.permanent = True
                flash("Your account has been created. Welcome to Itinerary Designer!", "success")
                return redirect(url_for("dashboard"))

    return render_template("register.html", error=error)


# 4. AUTHENTICATION: LOGOUT
@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been signed out safely.", "info")
    return redirect(url_for("login"))


# 5. USER DASHBOARD
@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    try:
        itin_rows = db.execute(
            """SELECT i.*, d.name AS destination_name FROM itineraries i
               LEFT JOIN destinations d ON d.id = i.destination_id
               WHERE i.owner_id = ? ORDER BY i.created_at DESC""",
            (current_user.user_id,),
        ).fetchall()
        itineraries = [dict(r) for r in itin_rows]
        saved = get_saved_destinations(current_user.user_id)
        dest_count = db.execute("SELECT COUNT(*) FROM destinations").fetchone()[0]
    finally:
        db.close()

    return render_template(
        "dashboard.html",
        itineraries=itineraries,
        saved=saved,
        destination_count=dest_count,
    )


# 6. DESTINATIONS CATALOG & HIMALAYAN EXPLORER MAP
@app.route("/destinations")
def destinations():
    search = request.args.get("q", "").strip()[:100]
    rows = list_destinations(search)
    return render_template("destinations.html", destinations=rows, search=search)


# 7. DESTINATION DETAIL (WEATHER FORECAST, HOTELS & HOMESTAYS, MAP, REVIEWS)
@app.route("/destinations/<slug>")
def destination_detail(slug):
    destination = get_destination_by_slug(slug)
    if not destination:
        abort(404)

    images = get_destination_images(destination["id"])
    activities = get_destination_activities(destination["id"])
    accommodations = get_accommodations(destination["id"])
    reviews = fetch_reviews(destination["id"])

    # Live High-Altitude Weather Forecast
    weather = fetch_weather_forecast(
        destination["latitude"],
        destination["longitude"],
        destination["name"],
    )

    # Check if user saved this destination
    saved = False
    if current_user.is_authenticated:
        db = get_db()
        try:
            saved = bool(
                db.execute(
                    "SELECT 1 FROM saved_destinations WHERE owner_id = ? AND destination_id = ?",
                    (current_user.user_id, destination["id"]),
                ).fetchone()
            )
        finally:
            db.close()

    return render_template(
        "destination_detail.html",
        destination=destination,
        images=images,
        activities=activities,
        accommodations=accommodations,
        reviews=reviews,
        weather=weather,
        saved=saved,
    )


# 8. TOGGLE SAVED DESTINATION
@app.route("/destinations/<slug>/save", methods=["POST"])
@login_required
def toggle_saved_destination(slug):
    destination = get_destination_by_slug(slug)
    if not destination:
        abort(404)

    db = get_db()
    try:
        existing = db.execute(
            "SELECT id FROM saved_destinations WHERE owner_id = ? AND destination_id = ?",
            (current_user.user_id, destination["id"]),
        ).fetchone()
        if existing:
            db.execute("DELETE FROM saved_destinations WHERE id = ?", (existing["id"],))
            flash(f"Removed {destination['name']} from your saved list.", "info")
        else:
            db.execute(
                "INSERT INTO saved_destinations (owner_id, destination_id, created_at) VALUES (?, ?, ?)",
                (current_user.user_id, destination["id"], now_iso()),
            )
            flash(f"Saved {destination['name']} to your bookmarked places!", "success")
        db.commit()
    finally:
        db.close()

    return redirect(url_for("destination_detail", slug=slug))


# 9. ADD DESTINATION REVIEW
@app.route("/destinations/<slug>/reviews", methods=["POST"])
@login_required
def add_destination_review(slug):
    destination = get_destination_by_slug(slug)
    if not destination:
        abort(404)

    review_text = request.form.get("review_text", "").strip()
    visit_date = request.form.get("visit_date", "").strip()
    try:
        rating = int(request.form.get("rating", "5"))
        if not 1 <= rating <= 5 or not 3 <= len(review_text) <= 2000:
            raise ValueError
        if visit_date:
            date.fromisoformat(visit_date)
    except ValueError:
        flash("Please provide a rating (1-5) and a review message between 3 and 2,000 characters.", "error")
        return redirect(url_for("destination_detail", slug=slug))

    db = get_db()
    try:
        now = now_iso()
        db.execute(
            """INSERT INTO reviews (owner_id, destination_id, rating, review_text, visit_date, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (current_user.user_id, destination["id"], rating, review_text, visit_date or None, now, now),
        )
        db.commit()
        flash("Thank you! Your Himalayan review has been posted.", "success")
    finally:
        db.close()

    return redirect(url_for("destination_detail", slug=slug))


# 10. SAVED DESTINATIONS LIST
@app.route("/saved-destinations")
@login_required
def saved_destinations():
    saved = get_saved_destinations(current_user.user_id)
    return render_template("saved_destinations.html", saved=saved)


# 11. MY ITINERARIES
@app.route("/my-itineraries")
@login_required
def my_itineraries():
    db = get_db()
    try:
        rows = db.execute(
            """SELECT i.*, d.name AS destination_name, a.name AS accommodation_name, a.type AS accommodation_type
               FROM itineraries i
               LEFT JOIN destinations d ON d.id = i.destination_id
               LEFT JOIN accommodations a ON a.id = i.accommodation_id
               WHERE i.owner_id = ? ORDER BY i.created_at DESC""",
            (current_user.user_id,),
        ).fetchall()
        itineraries = [dict(r) for r in rows]
    finally:
        db.close()
    return render_template("my_itineraries.html", itineraries=itineraries)


# 12. CREATE NEW ITINERARY
@app.route("/itineraries/new", methods=["GET", "POST"])
@login_required
def new_itinerary():
    destinations = list_destinations()
    if not destinations:
        flash("No destinations are currently available.", "error")
        return redirect(url_for("destinations"))

    db = get_db()
    try:
        acc_rows = db.execute("SELECT * FROM accommodations ORDER BY destination_id, rating DESC").fetchall()
        all_accommodations = [dict(r) for r in acc_rows]
    finally:
        db.close()

    if request.method == "POST":
        try:
            dest_id = int(request.form.get("destination_id", ""))
            acc_id = int(request.form.get("accommodation_id", "")) if request.form.get("accommodation_id") else None
            travelers = int(request.form.get("number_of_travelers", "1"))
            budget = float(request.form.get("budget", "0"))
            start_date = date.fromisoformat(request.form.get("start_date", ""))
            end_date = date.fromisoformat(request.form.get("end_date", ""))
            name = request.form.get("name", "").strip()
            style = request.form.get("travel_style", "Moderate")
            transport = request.form.get("transport_preference", "Train")
            acc_pref = request.form.get("accommodation_preference", "Homestay")

            if end_date < start_date:
                raise ValueError("Return date must be on or after departure date.")
            days = (end_date - start_date).days + 1
            if days > 30:
                raise ValueError("Itineraries can be up to 30 days.")
            if not 1 <= travelers <= 20:
                raise ValueError("Traveler count must be between 1 and 20.")
            if not 1 <= budget <= 10000000:
                raise ValueError("Budget must be between ₹1 and ₹10,000,000.")

            dest = next((d for d in destinations if d["id"] == dest_id), None)
            if not dest:
                raise ValueError("Selected destination is invalid.")

            trip_data = {
                "name": name or f"{dest['name']} Adventure",
                "destination_id": dest_id,
                "accommodation_id": acc_id,
                "destination": dest,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days,
                "number_of_travelers": travelers,
                "budget": budget,
                "travel_style": style,
                "transport_preference": transport,
                "accommodation_preference": acc_pref,
            }

            db = get_db()
            try:
                with db:
                    now = now_iso()
                    cur = db.execute(
                        """INSERT INTO itineraries (owner_id, name, destination_id, accommodation_id, start_date, end_date,
                                                   number_of_travelers, travel_style, transport_preference, accommodation_preference,
                                                   budget, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            current_user.user_id,
                            trip_data["name"],
                            dest_id,
                            acc_id,
                            trip_data["start_date"],
                            trip_data["end_date"],
                            travelers,
                            style,
                            transport,
                            acc_pref,
                            budget,
                            now,
                            now,
                        ),
                    )
                    itinerary_id = cur.lastrowid
                    write_itinerary_schedule(db, itinerary_id, trip_data)

                flash(f"Itinerary for {dest['name']} successfully generated and saved!", "success")
                return redirect(url_for("itinerary_detail", itinerary_id=itinerary_id))
            finally:
                db.close()
        except Exception as e:
            flash(f"Could not generate itinerary: {str(e)}", "error")

    # GET defaults
    selected_dest_id = request.args.get("destination", "")
    selected_acc_id = request.args.get("accommodation", "")
    trip_values = {
        "destination_id": selected_dest_id,
        "accommodation_id": selected_acc_id,
        "name": "",
    }
    preferences = get_user_preferences(current_user.user_id)

    return render_template(
        "itinerary_form.html",
        destinations=destinations,
        all_accommodations=all_accommodations,
        trip=trip_values,
        preferences=preferences,
        editing=False,
        heading="Design a New Himalayan Itinerary",
        action=url_for("new_itinerary"),
        submit_label="Generate Day-by-Day Itinerary",
        today=date.today().isoformat(),
        default_end=(date.today() + timedelta(days=3)).isoformat(),
        default_budget=20000,
        styles=TRAVEL_STYLES,
        transports=TRANSPORT_OPTIONS,
        accommodations_opts=ACCOMMODATION_OPTIONS,
    )


# 13. VIEW ITINERARY DETAIL (WITH WEATHER & MAP)
@app.route("/itineraries/<int:itinerary_id>")
@login_required
def itinerary_detail(itinerary_id):
    get_owned_itinerary_or_404(itinerary_id)
    trip = get_itinerary_detail(itinerary_id)
    if not trip:
        abort(404)

    destination = trip.get("destination") or {}
    accommodation = trip.get("accommodation")

    # Fetch weather for the destination
    weather = None
    if destination.get("latitude") and destination.get("longitude"):
        weather = fetch_weather_forecast(destination["latitude"], destination["longitude"], destination.get("name", ""))

    return render_template(
        "itinerary_detail.html",
        trip=trip,
        destination=destination,
        accommodation=accommodation,
        weather=weather,
    )


# 14. EDIT ITINERARY
@app.route("/itineraries/<int:itinerary_id>/edit", methods=["GET", "POST"])
@login_required
def edit_itinerary(itinerary_id):
    get_owned_itinerary_or_404(itinerary_id)
    existing = get_itinerary_detail(itinerary_id)
    destinations = list_destinations()

    db = get_db()
    try:
        acc_rows = db.execute("SELECT * FROM accommodations ORDER BY destination_id, rating DESC").fetchall()
        all_accommodations = [dict(r) for r in acc_rows]
    finally:
        db.close()

    if request.method == "POST":
        try:
            dest_id = int(request.form.get("destination_id", ""))
            acc_id = int(request.form.get("accommodation_id", "")) if request.form.get("accommodation_id") else None
            travelers = int(request.form.get("number_of_travelers", "1"))
            budget = float(request.form.get("budget", "0"))
            start_date = date.fromisoformat(request.form.get("start_date", ""))
            end_date = date.fromisoformat(request.form.get("end_date", ""))
            name = request.form.get("name", "").strip()
            style = request.form.get("travel_style", "Moderate")
            transport = request.form.get("transport_preference", "Train")
            acc_pref = request.form.get("accommodation_preference", "Homestay")

            days = (end_date - start_date).days + 1
            dest = next((d for d in destinations if d["id"] == dest_id), None)
            if not dest:
                raise ValueError("Destination not found.")

            trip_data = {
                "name": name or f"{dest['name']} Journey",
                "destination_id": dest_id,
                "accommodation_id": acc_id,
                "destination": dest,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days,
                "number_of_travelers": travelers,
                "budget": budget,
                "travel_style": style,
                "transport_preference": transport,
                "accommodation_preference": acc_pref,
            }

            db = get_db()
            try:
                with db:
                    db.execute(
                        """UPDATE itineraries
                           SET name = ?, destination_id = ?, accommodation_id = ?, start_date = ?, end_date = ?,
                               number_of_travelers = ?, travel_style = ?, transport_preference = ?,
                               accommodation_preference = ?, budget = ?, updated_at = ?
                           WHERE id = ? AND owner_id = ?""",
                        (
                            trip_data["name"],
                            dest_id,
                            acc_id,
                            trip_data["start_date"],
                            trip_data["end_date"],
                            travelers,
                            style,
                            transport,
                            acc_pref,
                            budget,
                            now_iso(),
                            itinerary_id,
                            current_user.user_id,
                        ),
                    )
                    write_itinerary_schedule(db, itinerary_id, trip_data, existing["days"], request.form)

                flash("Itinerary schedule and stay updates successfully saved!", "success")
                return redirect(url_for("itinerary_detail", itinerary_id=itinerary_id))
            finally:
                db.close()
        except Exception as e:
            flash(f"Could not update itinerary: {str(e)}", "error")

    preferences = get_user_preferences(current_user.user_id)
    return render_template(
        "itinerary_form.html",
        destinations=destinations,
        all_accommodations=all_accommodations,
        trip=existing,
        preferences=preferences,
        editing=True,
        heading=f"Edit: {existing['name']}",
        action=url_for("edit_itinerary", itinerary_id=itinerary_id),
        submit_label="Save Changes",
        today=date.today().isoformat(),
        default_end=(date.today() + timedelta(days=3)).isoformat(),
        default_budget=20000,
        styles=TRAVEL_STYLES,
        transports=TRANSPORT_OPTIONS,
        accommodations_opts=ACCOMMODATION_OPTIONS,
    )


# 15. DELETE ITINERARY
@app.route("/itineraries/<int:itinerary_id>/delete", methods=["POST"])
@login_required
def delete_itinerary(itinerary_id):
    get_owned_itinerary_or_404(itinerary_id)
    db = get_db()
    try:
        with db:
            db.execute("DELETE FROM itinerary_activities WHERE itinerary_day_id IN (SELECT id FROM itinerary_days WHERE itinerary_id = ?)", (itinerary_id,))
            db.execute("DELETE FROM itinerary_days WHERE itinerary_id = ?", (itinerary_id,))
            db.execute("DELETE FROM itineraries WHERE id = ? AND owner_id = ?", (itinerary_id, current_user.user_id))
        flash("Itinerary permanently deleted.", "info")
    finally:
        db.close()
    return redirect(url_for("my_itineraries"))


# 16. EXPORT ITINERARY TO TXT
@app.route("/itineraries/<int:itinerary_id>/export")
@login_required
def export_itinerary(itinerary_id):
    get_owned_itinerary_or_404(itinerary_id)
    trip = get_itinerary_detail(itinerary_id)
    dest = trip.get("destination") or {}
    acc = trip.get("accommodation")

    lines = [
        "HIMALAYAN TRAVEL ITINERARY DESIGNER",
        "=====================================",
        f"Trip Title: {trip['name']}",
        f"Destination: {dest.get('name', 'Himalayas')} ({dest.get('state', '')})",
        f"Elevation: {dest.get('elevation', 'N/A')}",
        f"Travel Dates: {trip['start_date']} to {trip['end_date']} ({len(trip.get('days', []))} Days)",
        f"Number of Travelers: {trip['number_of_travelers']}",
        f"Total Budget: INR {trip['budget']:,.0f}" if trip.get("budget") else "Budget: Not set",
        f"Travel Style: {trip.get('travel_style', 'Moderate')}",
        f"Transport: {trip.get('transport_preference', 'Train')}",
    ]

    if acc:
        lines.extend([
            "",
            "SELECTED ACCOMMODATION / STAY",
            "----------------------------",
            f"Property: {acc['name']} ({acc['type']})",
            f"Distance: {acc.get('distance', 'N/A')}",
            f"Rate: INR {acc['price_per_night']:,.0f} / night (Rating: {acc.get('rating', 'N/A')}⭐)",
            f"Amenities: {acc.get('amenities', 'N/A')}",
            f"Host Contact: {acc.get('phone', 'N/A')}",
        ])

    lines.extend([
        "",
        "DAY-BY-DAY ITINERARY PLAN",
        "-------------------------",
    ])

    for day in trip.get("days", []):
        lines.extend([
            "",
            f"DAY {day['day_number']} — {day['date']} : {day['title']}",
        ])
        if day.get("notes"):
            lines.append(f"  Notes & Advice: {day['notes']}")
        for act in day.get("activities", []):
            name = act.get("custom_name") or act.get("activity_name") or "Activity"
            time = f" [{act.get('start_time')}]" if act.get("start_time") else ""
            dur = f" ({act.get('duration')})" if act.get("duration") else ""
            cost = f" — INR {act.get('estimated_cost', 0):,.0f}" if act.get("estimated_cost") else " — Free"
            lines.append(f"  * {name}{time}{dur}{cost}")

    lines.extend([
        "",
        "=====================================",
        "Designed with Himalayan Travel Itinerary Designer",
        f"Exported: {datetime.now().strftime('%d %B %Y, %H:%M')}",
    ])

    clean_name = "".join(c if c.isalnum() else "_" for c in trip["name"]).strip("_") or "himalayan_trip_plan"
    return send_file(
        BytesIO("\n".join(lines).encode("utf-8")),
        mimetype="text/plain; charset=utf-8",
        as_attachment=True,
        download_name=f"{clean_name}.txt",
    )


# 17. TRAVEL PREFERENCES
@app.route("/preferences", methods=["GET", "POST"])
@login_required
def preferences():
    values = get_user_preferences(current_user.user_id)
    error = None
    if request.method == "POST":
        style = request.form.get("preferred_travel_style", "")
        budget = request.form.get("preferred_budget", "")
        acc = request.form.get("accommodation_preference", "")
        trans = request.form.get("transport_preference", "")
        notes = request.form.get("notes", "").strip()

        if len(notes) > 500:
            error = "Notes must be 500 characters or fewer."
        else:
            db = get_db()
            try:
                now = now_iso()
                existing = db.execute("SELECT id FROM travel_preferences WHERE owner_id = ? ORDER BY id DESC LIMIT 1", (current_user.user_id,)).fetchone()
                if existing:
                    db.execute(
                        """UPDATE travel_preferences
                           SET preferred_travel_style = ?, preferred_budget = ?, accommodation_preference = ?,
                               transport_preference = ?, notes = ?, updated_at = ?
                           WHERE id = ? AND owner_id = ?""",
                        (style, budget, acc, trans, notes, now, existing["id"], current_user.user_id),
                    )
                else:
                    db.execute(
                        """INSERT INTO travel_preferences (owner_id, preferred_travel_style, preferred_budget,
                                                          accommodation_preference, transport_preference, notes, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (current_user.user_id, style, budget, acc, trans, notes, now),
                    )
                db.commit()
                flash("Your travel preferences have been saved.", "success")
                return redirect(url_for("preferences"))
            finally:
                db.close()
        values = request.form

    return render_template(
        "preferences.html",
        values=values,
        error=error,
        styles=TRAVEL_STYLES,
        budgets=PREFERENCE_BUDGETS,
        accommodations=ACCOMMODATION_OPTIONS,
        transports=TRANSPORT_OPTIONS,
    )


# 18. ADMIN TELEMETRY
@app.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(404)

    db = get_db()
    try:
        counts = {
            "users": db.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            "destinations": db.execute("SELECT COUNT(*) FROM destinations").fetchone()[0],
            "accommodations": db.execute("SELECT COUNT(*) FROM accommodations").fetchone()[0],
            "itineraries": db.execute("SELECT COUNT(*) FROM itineraries").fetchone()[0],
        }
        destinations = list_destinations()
    finally:
        db.close()

    return render_template("admin.html", counts=counts, destinations=destinations)


# 19. API WEATHER ENDPOINT (AJAX HELPER)
@app.route("/api/weather")
def api_weather():
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    name = request.args.get("name", "Himalayas")
    data = fetch_weather_forecast(lat, lng, name)
    return jsonify(data)


# Error Handlers
@app.errorhandler(400)
def bad_request(_e):
    flash("Your request session expired or was rejected. Please try again.", "error")
    return redirect(url_for("login"))


@app.errorhandler(404)
def not_found(_e):
    return render_template("base.html"), 404


@app.errorhandler(500)
def server_error(_e):
    return render_template("base.html"), 500


if __name__ == "__main__":
    seed_database()
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in {"1", "true", "yes"}
    print("\n" + "=" * 65)
    print("🏔️  HIMALAYAN TRAVEL ITINERARY DESIGNER SERVER STARTED")
    print(f"👉  Open your browser at: http://{host}:{port}/")
    print(f"🛡️  Admin Account:           {Config.ADMIN_USERNAME} / {Config.ADMIN_PASSWORD}")
    print("=" * 65 + "\n")
    app.run(host=host, port=port, debug=debug)
