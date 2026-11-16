document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("current-location");
  if (!btn) return;
  const input = document.getElementById("start_location");
  const status = document.getElementById("location-status");
  btn.addEventListener("click", () => {
    if (!navigator.geolocation) {
      status.textContent = "Location is not supported by this browser. Please type your pickup location.";
      return;
    }
    btn.disabled = true;
    btn.textContent = "Finding location…";
    status.textContent = "Please allow location access in your browser.";
    navigator.geolocation.getCurrentPosition(async (position) => {
      const lat = position.coords.latitude;
      const lon = position.coords.longitude;
      // Coordinates are a valid fallback if reverse geocoding is unavailable.
      input.value = `${lat.toFixed(6)}, ${lon.toFixed(6)}`;
      status.textContent = "Current coordinates found. Looking up the place name…";
      try {
        const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}`;
        const response = await fetch(url, { headers: { "Accept": "application/json" } });
        if (response.ok) {
          const data = await response.json();
          if (data.display_name) input.value = data.display_name;
        }
        status.textContent = "Pickup location filled from your current location.";
      } catch (e) {
        status.textContent = "Coordinates filled. You can continue with this pickup location.";
      }
      btn.disabled = false;
      btn.textContent = "◎ Use current location";
    }, (error) => {
      const messages = {
        1: "Location permission was denied. Allow location access in your browser settings.",
        2: "Your location is currently unavailable. Please type the pickup location.",
        3: "Location request timed out. Please try again."
      };
      status.textContent = messages[error.code] || "Could not get your location. Please type it manually.";
      btn.disabled = false;
      btn.textContent = "◎ Use current location";
    }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 });
  });
});
