import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "himalayan-secret-key-2026-prod-ready-token"
    DB_PATH = os.environ.get("DB_PATH") or os.path.join(BASE_DIR, "itinerarydesigner.db")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "").lower() in {"1", "true", "yes"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # Admin Account
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "arpit.06")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "arpitchoudhary3406@gmail.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "@Arpit06")
    ADMIN_NAME = os.environ.get("ADMIN_NAME", "arpit.06")
    
    # Open-Meteo Weather API
    OPEN_METEO_API_URL = "https://api.open-meteo.com/v1/forecast"
