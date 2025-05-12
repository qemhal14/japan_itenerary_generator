# TemanTravel 🗺️

**TemanTravel** is an interactive command-line tool that helps you generate daily travel itineraries in Japan based on your interests and duration of stay. It fetches real points of interest using OpenStreetMap and generates a realistic daily plan.

---

## 🚀 Current Version

**`pre-alpha`**  
This is still pre-alpha, built to test the core functionality.

---

## ✨ Features

- Interactive user input: choose region, number of days, and travel interests.
- Automatic place selection using real data from OpenStreetMap.
- Clustering algorithm (KMeans) to divide locations across days.
- Basic map visualization for each day using Folium.
- Realistic distribution of places (currently 4 places/day max).
- Graceful error handling and retry options.

---

## 🛠 Requirements

- Python 3.7+
- Packages:
  - `osmnx`
  - `pandas`
  - `geopy`
  - `scikit-learn`
  - `folium`
