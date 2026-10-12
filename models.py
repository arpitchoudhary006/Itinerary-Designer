import sqlite3
from datetime import datetime, timezone
from flask_login import UserMixin
from config import Config

class User(UserMixin):
    def __init__(self, row):
        data = dict(row) if row is not None else {}
        self.id = data.get("id")
        self.user_id = data.get("user_id")
        self.name = data.get("name")
        self.email = data.get("email")
        self.role = data.get("role", "USER")
        self.organization_id = data.get("organization_id") or "org_default"

    def get_id(self):
        return str(self.id)

    @property
    def is_admin(self):
        return self.role in {"ADMIN", "OWNER"}


SQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    organization_id TEXT DEFAULT 'org_default',
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'USER',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS destinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    state TEXT,
    description TEXT,
    duration TEXT,
    difficulty TEXT,
    elevation TEXT,
    best_time TEXT,
    estimated_budget REAL,
    latitude REAL,
    longitude REAL,
    organization_id TEXT DEFAULT 'org_default',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS destination_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination_id INTEGER NOT NULL,
    image_url TEXT NOT NULL,
    caption TEXT,
    is_primary INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY(destination_id) REFERENCES destinations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    duration TEXT,
    estimated_cost REAL,
    difficulty TEXT,
    category TEXT,
    image_url TEXT,
    latitude REAL,
    longitude REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(destination_id) REFERENCES destinations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS accommodations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- 'Hotel' or 'Homestay' or 'Eco Camp'
    price_per_night REAL NOT NULL,
    rating REAL NOT NULL,
    reviews_count INTEGER DEFAULT 0,
    distance TEXT,
    amenities TEXT,
    phone TEXT,
    booking_url TEXT,
    description TEXT,
    image_url TEXT,
    latitude REAL,
    longitude REAL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(destination_id) REFERENCES destinations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS itinerary_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    day_count INTEGER,
    template_data TEXT,
    estimated_budget REAL,
    last_updated TEXT NOT NULL,
    FOREIGN KEY(destination_id) REFERENCES destinations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS itineraries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id TEXT NOT NULL,
    name TEXT NOT NULL,
    destination_id INTEGER,
    accommodation_id INTEGER,
    start_date TEXT,
    end_date TEXT,
    number_of_travelers INTEGER DEFAULT 1,
    travel_style TEXT,
    transport_preference TEXT,
    accommodation_preference TEXT,
    budget REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(destination_id) REFERENCES destinations(id),
    FOREIGN KEY(accommodation_id) REFERENCES accommodations(id)
);

CREATE TABLE IF NOT EXISTS itinerary_days (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    itinerary_id INTEGER NOT NULL,
    day_number INTEGER NOT NULL,
    date TEXT,
    title TEXT,
    notes TEXT,
    FOREIGN KEY(itinerary_id) REFERENCES itineraries(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS itinerary_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    itinerary_day_id INTEGER NOT NULL,
    activity_id INTEGER,
    custom_name TEXT,
    start_time TEXT,
    duration TEXT,
    estimated_cost REAL,
    notes TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(itinerary_day_id) REFERENCES itinerary_days(id) ON DELETE CASCADE,
    FOREIGN KEY(activity_id) REFERENCES activities(id)
);

CREATE TABLE IF NOT EXISTS saved_destinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id TEXT NOT NULL,
    destination_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(owner_id, destination_id),
    FOREIGN KEY(destination_id) REFERENCES destinations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id TEXT NOT NULL,
    destination_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    review_text TEXT NOT NULL,
    visit_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(destination_id) REFERENCES destinations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS travel_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id TEXT NOT NULL,
    preferred_travel_style TEXT,
    preferred_budget TEXT,
    accommodation_preference TEXT,
    transport_preference TEXT,
    notes TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id TEXT NOT NULL,
    note_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def get_db():
    db = sqlite3.connect(Config.DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db():
    db = get_db()
    try:
        db.executescript(SQL_SCHEMA)
        db.commit()
    finally:
        db.close()


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def row_to_dict(row):
    return dict(row) if row else None
