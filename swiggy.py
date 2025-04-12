import requests 
import json
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.swiggy.com/',
}

def fetch_swiggy_data(lat, lng, food_preference, food_type):
    """Fetch restaurant and food data from Swiggy API."""
    print(f"🔎 Searching Swiggy for {food_preference} ({food_type}) at {lat}, {lng}...")

    food_filter = "&vegOnly=true" if food_type == "veg" else ""  # Apply filter only if veg
    api_url = f"https://www.swiggy.com/dapi/restaurants/search/v3?lat={lat}&lng={lng}&str={food_preference}{food_filter}&submitAction=ENTER"

    try:
        response = requests.get(api_url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        extracted_data = []

        if "data" in data and "cards" in data["data"]:
            for card in data["data"]["cards"]:
                grouped_card = card.get("groupedCard", {}).get("cardGroupMap", {}).get("DISH", {}).get("cards", [])

                for dish_card in grouped_card:
                    dish_info = dish_card.get("card", {}).get("card", {}).get("info", {})
                    restaurant_info = dish_card.get("card", {}).get("card", {}).get("restaurant", {}).get("info", {})

                    if dish_info:
                        dish_details = {
                            "Dish Name": dish_info.get("name"),
                            "Category": dish_info.get("category"),
                            "Price (INR)": dish_info.get("price", 0) / 100,
                            "Rating": dish_info.get("ratings", {}).get("aggregatedRating", {}).get("rating"),
                            "Is Veg": "Yes" if dish_info.get("isVeg") else "No",
                            "Restaurant Name": restaurant_info.get("name"),
                            "Address": restaurant_info.get("address"),
                            "Delivery Time": restaurant_info.get("sla", {}).get("deliveryTime", float("inf"))  # Use inf if not available
                        }

                        # Filter dishes based on the user's preference
                        if food_type == "veg" and dish_details["Is Veg"] == "Yes":
                            extracted_data.append(dish_details)
                        elif food_type == "non-veg" and dish_details["Is Veg"] == "No":
                            extracted_data.append(dish_details)
                        elif food_type == "both":
                            extracted_data.append(dish_details)

        print(f"✅ Found {len(extracted_data)} food items from Swiggy.")
        '''with open('swiggy_results.json', 'w') as file:
            json.dump(extracted_data, file, indent=4)'''
        with open('rag_results.json', 'w') as file:
            json.dump(extracted_data, file, indent=4)
        print("💾 Data has been saved to temp_results.json")
        return extracted_data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data from Swiggy API: {e}")
        return []

