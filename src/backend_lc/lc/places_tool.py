import os
import requests # For making HTTP requests
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from typing import List, Dict, Optional

# --- Google Places API Tool ---

# Load your API key from an environment variable for security
# Set this environment variable in your system or .env file
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_API_KEY")

class QueryPlaceInfoArgs(BaseModel):
    query: str = Field(..., description="The search query for the place, e.g., 'Abaci in Denton', 'coffee shops near Cross Roads Texas'. Be as specific as possible.")
    # You could add optional location bias parameters here later if needed, e.g., latitude, longitude

@tool(args_schema=QueryPlaceInfoArgs)
def query_place_information(query: str) -> List[Dict] | str:
    """
    Searches for places (businesses, points of interest) using Google Places API 
    to find details like name, address, current opening status, and operating hours.
    Provide a specific query including the name and location of the place.
    """
    if not GOOGLE_PLACES_API_KEY:
        return "Error: Google Places API key is not configured. Please set the GOOGLE_PLACES_API_KEY environment variable."
    if not query:
        return "Error: Search query cannot be empty."

    print(f"Querying Google Places API for: {query}")

    # Using Google Places API - Text Search endpoint
    # https://developers.google.com/maps/documentation/places/web-service/search-text
    search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    
    # Parameters for the Text Search request
    # We are requesting specific fields to get opening hours and business status
    # For field masks, see: https://developers.google.com/maps/documentation/places/web-service/place-data-fields
    # While Text Search doesn't use a 'fields' parameter directly like Place Details,
    # the default response for Text Search usually includes enough basic info.
    # For more detail like `open_now`, we often need a Place ID and a subsequent Place Details request.
    # Let's try to get Place ID first with Text Search, then get details.
    
    params_search = {
        'query': query,
        'key': GOOGLE_PLACES_API_KEY,
    }

    place_results = []

    try:
        response_search = requests.get(search_url, params=params_search, timeout=10)
        response_search.raise_for_status() # Raise an exception for HTTP errors
        search_data = response_search.json()

        if search_data.get("status") != "OK" and search_data.get("status") != "ZERO_RESULTS":
            return f"Error from Google Places API (Text Search): {search_data.get('status')} - {search_data.get('error_message', '')}"
        
        if not search_data.get("results"):
            return f"No places found for query: '{query}'"

        # Process up to a few results to get their details
        for place_summary in search_data.get("results", [])[:3]: # Limit to top 3 results
            place_id = place_summary.get("place_id")
            if not place_id:
                continue

            # Now make a Place Details request for each place_id to get opening_hours
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            params_details = {
                'place_id': place_id,
                'fields': "name,formatted_address,opening_hours,business_status,permanently_closed", # Essential fields
                'key': GOOGLE_PLACES_API_KEY
            }
            response_details = requests.get(details_url, params=params_details, timeout=10)
            response_details.raise_for_status()
            details_data = response_details.json()

            if details_data.get("status") != "OK":
                print(f"Could not get details for place_id {place_id}: {details_data.get('status')}")
                continue
            
            place_detail = details_data.get("result", {})
            
            is_open_now = None
            opening_hours_text = ["Opening hours not available."]
            business_status = place_detail.get("business_status", "UNKNOWN")

            if place_detail.get("permanently_closed"):
                business_status = "PERMANENTLY_CLOSED"
                is_open_now = False
                opening_hours_text = ["Permanently Closed."]
            elif "opening_hours" in place_detail:
                hours_info = place_detail["opening_hours"]
                is_open_now = hours_info.get("open_now") # This is a boolean
                if "weekday_text" in hours_info:
                    opening_hours_text = hours_info["weekday_text"] # This is a list of strings
            
            place_info = {
                "name": place_detail.get("name", "N/A"),
                "address": place_detail.get("formatted_address", "N/A"),
                "is_open_now": is_open_now, # true, false, or None if not available
                "opening_hours_text": opening_hours_text, # List of strings like "Monday: 9 AM - 5 PM"
                "business_status": business_status # e.g., OPERATIONAL, CLOSED_TEMPORARILY
            }
            place_results.append(place_info)

        if not place_results:
             return f"No detailed place information found for query: '{query}' (perhaps Place IDs were missing or details couldn't be fetched)."
        return place_results

    except requests.exceptions.Timeout:
        return f"Error: Request timed out while contacting Google Places API for '{query}'."
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Google Places API for '{query}': {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred while querying place information for '{query}': {str(e)}"