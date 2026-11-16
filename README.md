# Hanuman Travels — Python Flask Website

A beginner-friendly transport booking website built with Python, Flask, SQLite, HTML, CSS and JavaScript.

## Features
- Attractive landing page with separate Admin Login and Customer Login.
- Customer registration and secure password hashing.
- Admin can add transport vehicles with vehicle type, capacity, base location and per-kilometre rate.
- Customers can enter a starting location, use **Use current location**, choose/type a destination, select a vehicle and request a booking.
- Route distance is requested from OpenStreetMap's public services. If the routing service is unavailable, the app falls back to straight-line distance (clearly an estimate).
- Estimated fare = distance × vehicle rate per km.
- Admin can see booking details and Accept or Reject each request.
- Customers can see their booking status.

## Requirements
- Python 3.10 or newer
- Internet connection for location lookup and route estimation
- A browser that allows location access (localhost is normally treated as a secure context)

## Step-by-step setup (Mac)
1. Download and unzip `Hanuman_Travels.zip`.
2. Open **Terminal**.
3. Move into the project folder. If it is in Downloads, run:
   ```bash
   cd ~/Downloads/hanuman_travels
   ```
   If the folder is elsewhere, type `cd ` (with a space), drag the unzipped folder into Terminal, then press Enter.
4. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```
5. Activate it:
   ```bash
   source venv/bin/activate
   ```
6. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
7. Start the website:
   ```bash
   python app.py
   ```
8. Open this address in your browser:
   `http://127.0.0.1:5000`

## Demo admin login
- Email: `admin@hanumantravels.com`
- Password: `Admin@123`

Customers should choose **Customer Login → Create an account** and register with their own email/password.

## How to test
1. Sign in as admin.
2. Add a vehicle (for example, a Sedan based in Bengaluru at ₹14 per km).
3. Log out and register/sign in as a customer.
4. On the customer page, enter the starting point or press **Use current location** and allow browser location permission.
5. Enter a destination, select a vehicle and travel date, then submit the booking.
6. Log out and sign in as admin. The booking appears in the Booking Requests section.
7. Press **Accept** or **Reject**. The customer sees the updated status on their dashboard.

## Current location troubleshooting
- Open the site at `http://127.0.0.1:5000`, not by double-clicking an HTML file.
- Press **Use current location** and choose **Allow** when the browser asks for location permission.
- On macOS, check System Settings → Privacy & Security → Location Services and allow location access for your browser.
- If permission was denied earlier, click the icon beside the website address in the browser and reset Location permission, then reload.
- If location access is unavailable, type a starting location manually.
- The button uses browser geolocation and OpenStreetMap reverse lookup. The location is only used to fill the start field for this booking; this demo does not store continuous tracking.

## Notes and production safety
- The demo uses SQLite, so you do not need to install MySQL.
- Distance/fare are estimates. The public OpenStreetMap/OSRM demo services can be rate-limited or unavailable; always confirm the actual route and fare before travel.
- For a real business deployment, configure a strong `SECRET_KEY`, use HTTPS, add CSRF protection, validate passenger capacity and dates, and use a managed routing/geocoding service with its terms and limits reviewed.
- Change the demo admin password before using this outside a local demo.
