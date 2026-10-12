#!/usr/bin/env python3
"""
Launcher for Himalayan Travel Itinerary Designer.
Initializes database, seeds demo accounts, and runs Flask web server.
"""

import os
import sys
import webbrowser
import threading
import time

# Ensure current directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app import app, seed_database
from config import Config

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:5000/login")

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🏔️   HIMALAYAN TRAVEL ITINERARY DESIGNER")
    print("=" * 70)
    print("  Initializing SQLite database & Himalayan presets...")
    seed_database()
    print("  Database verified and seeded successfully!\n")
    print("  🛡️ Admin Account:")
    print(f"     Username: {Config.ADMIN_USERNAME}  |  Password: {Config.ADMIN_PASSWORD}")
    print("\n  👉 Starting local web server at: http://127.0.0.1:5000/ (Starts at Login page)")
    print("=" * 70 + "\n")

    # Optionally launch browser in a thread
    if os.environ.get("AUTO_OPEN_BROWSER", "1") == "1":
        threading.Thread(target=open_browser, daemon=True).start()

    app.run(host="127.0.0.1", port=5000, debug=False)
