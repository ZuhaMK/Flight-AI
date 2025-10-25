# Modified Flight API logic integrated for use as a Tool
def get_flight_prices(origin: str, destination: str, date: str = None) -> str:
    """
    Calls the Travel Payouts API to get flight prices.
    
    Args:
        origin: The IATA code for the departure city (e.g., 'DXB').
        destination: The IATA code for the arrival city (e.g., 'LON').
        date: The departure date in YYYY-MM-DD format (optional).
        
    Returns:
        A JSON string of the flight data or an error message.
    """
    import os
    import requests
    from dotenv import load_dotenv
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    import json # Import for JSON dumping
    
    # Reload env vars in function if not sure of scope
    load_dotenv()
    TOKEN = os.getenv("TRAVEL_PAYOUTS_API_TOKEN")
    if not TOKEN:
        return json.dumps({"error": "Missing API token for flight service."})

    url = "https://api.travelpayouts.com/v2/prices/latest"
    # Note: Travelpayouts uses IATA codes. You might need a pre-processor 
    # if the LLM extracts full city names.
    params = {
        "origin": origin, 
        "destination": destination, 
        "token": TOKEN
        # 'depart_date': date, # Uncomment and use if your API supports date
    }

    s = requests.Session()
    # Retry logic...
    s.mount("https://", HTTPAdapter(max_retries=Retry(
        total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504]
    )))

    try:
        r = s.get(url, params=params, timeout=10)
        r.raise_for_status()
        # Return the JSON string of the flight data
        return json.dumps(r.json())
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Flight API network problem: {e}"})

# A mapping of available functions
available_tools = {
    "get_flight_prices": get_flight_prices,
}