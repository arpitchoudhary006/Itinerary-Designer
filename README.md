# 🗺️ Itinerary Designer

A production-ready Flask web application for travel planning with **Administrator Panel CRUD Management**, **dynamic hotel management (Budget/Standard/Luxury)**, **nearby tourist attractions management**, **estimated sightseeing time calculations**, **live weather forecasting**, and **interactive Leaflet maps**.

---

## 🌟 Key Features

1. **Administrator Panel Management (Full CRUD)**:
   - Complete management of **Destinations**, **Hotels & Accommodations**, and **Nearby Visiting Places** directly through the UI.
   - Add, edit, delete, and view records dynamically with confirmation modals and validation.
   - Categorize hotels as *Budget*, *Standard*, and *Luxury*, manage availability, contact details, pricing, and amenities.
   - Never need to edit HTML code to update hotels, places, or destinations.

2. **Simplified Plan Your Trip (Estimated Sightseeing Time)**:
   - Removed the rigid number-of-days requirement.
   - Dynamically calculates:
     - Main destination sightseeing time (e.g. 4–5 hours)
     - Selected nearby attractions time (e.g. Solang Valley: 2–3 hours, Hadimba Temple: 1 hour)
     - Total estimated sightseeing time required to explore the place.
     - Suggested sightseeing sequence and schedule.

3. **Nearby Visiting Places & Tourist Attractions**:
   - Each destination displays its own nearby attractions in an attractive card-based layout.
   - Shows location, visiting hours, distance, entry fee, best time to visit, and images.

4. **Verified Hotels, Homestays & Resorts**:
   - Filter by *All Stays*, *Budget*, *Standard*, or *Luxury*.
   - Direct phone contact, price per night in INR, and availability status.

5. **Weather Forecasting & Mountain Advisories**:
   - Real-time weather data with temperature, humidity, wind speed, and 7-day forecast.

6. **Interactive Leaflet Mountain Maps**:
   - Interactive maps with terrain relief, destination summits, and hotel pins.

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
