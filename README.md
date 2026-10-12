# 🏔️ Himalayan Travel Itinerary Designer

A production-ready Flask web application for planning high-altitude Himalayan journeys with **interactive topographic Leaflet maps**, **live weather forecasting with mountain safety advisories**, **verified nearby hotels & rustic homestays**, and **multi-day customized itinerary generation**.

---

## 🌟 Key Features

1. **Starts with Himalayan Login Experience**:
   - The root website (`/`) directs unauthenticated users straight to the login page as requested.
   - Clean, secure login form supporting sign-in via username or email.
   - Guest exploration link allows previewing destinations before signing up.

2. **Verified Nearby Hotels, Homestays & Alpine Camps**:
   - Dedicated accommodation database with price per night (INR), traveler ratings, distance from trailheads/centers, amenities chips (e.g., *Garhwali Thali, Heated Rooms, Campfire, Guided Trek*), phone numbers, and direct host booking.
   - Interactive filtering on destination pages: `All Stays`, `Homestays`, `Hotels & Resorts`, and `Eco Camps`.
   - Seamlessly select preferred accommodations when designing an itinerary!

3. **High-Altitude Weather Forecasting & Safety Advisories**:
   - Integrates live meteorological data from Open-Meteo's high-resolution global weather model (WMO codes).
   - Real-time current temperature, apparent "feels like" temp, humidity, and ridge wind speeds.
   - 7-Day weather forecast cards with high/low temperatures and precipitation probabilities.
   - **Automated Alpine Safety Advisory Generator**: warns of sub-zero freezes, high-altitude wind gusts, rain/snow precautions, and ideal morning summit departure hours.
   - Built-in resilient seasonal mountain model fallback ensures the app works seamlessly even without an active internet connection.

4. **Interactive Leaflet Mountain Maps**:
   - **Destination Detail Map**: Plots destination summits, nearby hotels (emerald pin), homestays (purple pin), and activity trailheads (blue pin) with interactive popups and one-click filtering.
   - **Dual Layer Toggle**: Switch between clean street maps and **Topographic Terrain Relief** (contours, passes, and high mountain ridges).
   - **Himalayan Regional Explorer Map**: Pan across Uttarakhand and Himachal Pradesh on the destinations catalog page.

5. **Day-by-Day Itinerary Generator & Exporter**:
   - Customize trip duration, travelers (1–20), budget (INR), transport preference, and stay style.
   - Automatic activity timeline generation with times, durations, and costs.
   - Full day-by-day editor to adjust daily titles, route notes, and custom activities.
   - **One-Click TXT Export**: Download printable, clean itinerary summaries for offline trail reference.

---

## 📂 Project Folder Structure

```
Himalayan_Travel_Itinerary_Designer/
├── app.py                     # Master Flask web application & routes
├── config.py                  # Security, database path & demo credentials
├── models.py                  # SQLite relational schema & User model
├── run.py                     # Python runner script (auto browser launch)
├── run.bat                    # 1-Click Windows batch launcher
├── requirements.txt           # Python package dependencies
├── README.md                  # Complete documentation
├── services/
│   ├── data_presets.py        # Destinations, activities, templates, and nearby hotels/homestays
│   └── weather_service.py     # Live Open-Meteo weather forecast & alpine safety advisory engine
├── static/
│   ├── css/
│   │   └── style.css          # Alpine-themed responsive CSS (glassmorphism, cards, pins)
│   └── js/
│       └── map.js             # Leaflet map helper with custom markers, popups & layer switch
└── templates/
    ├── base.html              # Core navigation layout, user badge, and alerts
    ├── login.html             # High-impact login with 1-click demo buttons
    ├── register.html          # Traveler registration
    ├── dashboard.html         # User dashboard with recent trips & stats
    ├── destinations.html      # Catalog with search & Himalayan Explorer Map
    ├── destination_detail.html# Weather widget, hotel/homestay directory, map & reviews
    ├── itinerary_form.html    # Itinerary creator/editor with stay selection
    ├── itinerary_detail.html  # Day-by-day plan with stay spotlight & weather
    ├── my_itineraries.html    # User's trips list with view/edit/delete/export
    ├── saved_destinations.html# Bookmarked places
    ├── preferences.html       # Default travel style & budget settings
    └── admin.html             # System telemetry & destination overview
```

---

## 🚀 How to Run

### Method 1: Using the 1-Click Windows Batch Script
Simply double-click:
```bat
run.bat
```

### Method 2: Using Python
Open your terminal inside this folder and run:
```bash
python run.py
```
Or directly with Flask:
```bash
python app.py
```

Open your browser at:
👉 **`http://127.0.0.1:5000/`** (Directly starts with the Login page)

---

## 🛡️ Admin Account Credentials

Sign in to access the full admin dashboard and telemetry:

| Role | Username | Password | Email |
|---|---|---|---|
| **Admin** | `arpit.06` | `@Arpit06` | `arpit.06@himalayas.com` |

---

## 🗺️ Covered Himalayan Destinations

- **Tungnath & Chandrashila** (Chopta, Uttarakhand) — 4,000 m
- **Badrinath & Mana Valley** (Garhwal, Uttarakhand) — 3,133 m
- **Hemkund Sahib & Valley of Flowers** (Chamoli, Uttarakhand) — 4,632 m
- **Mussoorie & Landour** (Uttarakhand) — 2,275 m
- **Triund Trek & McLeod Ganj** (Dharamshala, Himachal Pradesh) — 2,850 m
- **Kasauli Heritage & Forest Trails** (Himachal Pradesh) — 1,900 m
