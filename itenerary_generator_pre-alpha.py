# Modules
import osmnx as ox
import pandas as pd
from geopy.distance import geodesic
from sklearn.cluster import KMeans
import time
import folium
from folium.plugins import AntPath
import os

# List of options user can choose
interests_options = {
    "1": "Culture & History",
    "2": "Nature & Parks",
    "3": "Shopping",
    "4": "Culinary",
    "5": "Temples & Places of Worship",
    "6": "Museums & Galleries",
    "7": "City Views",
    "8": "Family Activities"
}

# List of interests and corresponding OSM tags
interest_to_tags = {
    "1": {'historic': ['castle', 'monument', 'memorial'], 'tourism': ['attraction', 'museum']},
    "2": {'leisure': ['park', 'garden', 'nature_reserve'], 'natural': 'wood'},
    "3": {'shop': ['mall', 'department_store', 'clothes', 'supermarket']},
    "4": {'amenity': ['restaurant', 'cafe', 'fast_food'], 'cuisine': True},  
    "5": {'amenity': ['place_of_worship'], 'religion': ['shinto', 'buddhist']},
    "6": {'tourism': ['museum', 'gallery']},
    "7": {'tourism': ['viewpoint'], 'man_made': ['tower']},
    "8": {'leisure': ['zoo', 'aquarium'], 'tourism': 'theme_park'}
}

# Function to get user input with validation
def user_inp(prompt, options):
    user_input = input(prompt)
    while user_input not in options:
        print("Invalid input. Please try again.")
        user_input = input(prompt)
    return user_input

# Function to get places based on user input
def get_places(city_name, num_places, selected_interest_key):
    print(f"\nFetching points of interest in: {city_name}")
    try:
        start = time.time()
        tags = interest_to_tags.get(selected_interest_key, {'tourism': 'attraction'})
        gdf = ox.features_from_place(city_name, tags)

        gdf = gdf[['name', 'geometry']].dropna()
        gdf = gdf[gdf['geometry'].geom_type == 'Point']
        gdf['lat'] = gdf.geometry.y
        gdf['lon'] = gdf.geometry.x
        gdf = gdf.drop_duplicates(subset=['name'])
        gdf = gdf.head(num_places)
        df = gdf[['name', 'lat', 'lon']].dropna().reset_index(drop=True)

        print(f"Found {len(df)} places. Fetch time: {round(time.time() - start, 2)} seconds")
        return df
    except Exception as e:
        print("Failed to fetch places:", e)
        return None

# Function to generate itinerary and cluster the places
def generate_itinerary(df, days, max_per_day=6):
    print(f"\nClustering {len(df)} places into {days} days...")
    coords = df[['lat', 'lon']]
    kmeans = KMeans(n_clusters=days, random_state=42).fit(coords)
    df['day'] = kmeans.labels_ + 1

    filtered_rows = []
    for day in range(1, days + 1):
        day_df = df[df['day'] == day]
        if len(day_df) > max_per_day:
            day_df = day_df.sample(max_per_day, random_state=42)  
        filtered_rows.append(day_df)

    itinerary = pd.concat(filtered_rows).sort_values(by=['day', 'name']).reset_index(drop=True)
    return itinerary

# Function to display itinerary
def display_itinerary(itinerary, days):
    print("\nItinerary Recommendation:\n")
    for day in range(1, days + 1):
        print(f"Day {day}")
        print("-" * 30)
        day_df = itinerary[itinerary['day'] == day]
        for i, row in day_df.iterrows():
            print(f"{i + 1}. {row['name']} ({row['lat']:.4f}, {row['lon']:.4f})")
        print("")

# Function to display map
def create_day_map(itenerary, day, save_dir="maps"):
    day_df = itenerary[itenerary['day'] == day]
    if day_df.empty:
        print(f"No places found for Day {day}.")
        return
    
    # Starting point
    start_lat, start_lon = day_df.iloc[0][['lat', 'lon']]
    # Create base map
    m = folium.Map(location=[start_lat, start_lon], zoom_start=13)
    # Add markers and collect routes
    route_coords = []
    for i, row in day_df.iterrows():
        coord = [row['lat'], row['lon']]
        route_coords.append(coord)
        folium.Marker(
            location=coord,
            popup=f"{i+1}. {row['name']}",
            tooltip=row['name'],
            icon=folium.Icon(color='blue', icon="info-sign")
        ).add_to(m)
    AntPath(route_coords, color="green", weight=2.5, opacity=1).add_to(m)
    # Save map to html
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"day_{day}_map.html")
    m.save(file_path)
    print(f"Map for Day {day} saved to {file_path}")

# Main Program
if __name__ == "__main__":
    print("Welcome to TemanTravel: Itinerary Generator for Traveling in Japan\n")

    # Input Area
    while True:
        prefecture = input("Enter the name of a prefecture in Japan (e.g., Tokyo, Osaka, Hokkaido): ").strip().title()
        area = input(f"Enter the name of an area in {prefecture}: ").strip().title()
        city = f"{area}, {prefecture}, Japan"

        # Input number of days
        while True:
            day_input = input("How many days do you want your itinerary to be? (e.g., 3): ").strip()
            try:
                total_days = int(day_input)
                if total_days < 1:
                    print("Number of days must be >= 1. Please try again.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a number like 1, 2, 3, etc.")

        # Input interest selection
        print("\nWhat is your main interest during this trip?")
        for key, val in interests_options.items():
            print(f"{key}. {val}")
        selected_interest = user_inp("Enter your interest number (e.g., 1): ", interests_options.keys())

        # Get places based on user input
        max_places_per_day = 6
        place_limit = total_days * max_places_per_day
        df_places = get_places(city_name=city, num_places=place_limit, selected_interest_key=selected_interest)
        if df_places is None:
            choice = user_inp("Failed to fetch data. Try again or exit? (r = retry / e = exit): ", ["r", "e"]).strip().lower()
            if choice == 'e':
                print("Thank you for using TemanTravel. Goodbye!")
                break
            else:
                continue
        
        # Validate the number of places
        if len(df_places) < total_days * 3: # Minimum 3 places per day
            print(f"\nOnly {len(df_places)} places found, which is too few for {total_days} days.")
            choice = user_inp("Try another area or exit? (r = retry / e = exit): ", ["r", "e"]).strip().lower()
            if choice == 'e':
                print("Thank you for using TemanTravel. Goodbye!")
                break
            else:
                continue

        # Confirmation
        print("\nAll inputs are valid.")
        print("1) Generate itinerary")
        print("2) Try another area")
        print("3) Exit")
        final_choice = user_inp("Choose an option (1/2/3): ", ["1", "2", "3"]).strip()
        if final_choice == '2':
            continue
        elif final_choice == '3':
            print("Thank you for using TemanTravel. Goodbye!")
            break

        # Generate and display itinerary
        itinerary = generate_itinerary(df_places, days=total_days, max_per_day=6)
        display_itinerary(itinerary, total_days)

        # Generate maps
        for day in range(1, total_days + 1):
            create_day_map(itinerary, day)
            print(f"Map for Day {day} saved.")

        # Ask for next action
        print("What would you like to do next?")
        print("1) Create another itinerary")
        print("2) Exit")
        next_action = user_inp("Choose an option (1/2): ", ["1", "2"])

        if next_action == "2":
            print("Thank you for using TemanTravel. Enjoy your trip!")
            break
        else:
            continue