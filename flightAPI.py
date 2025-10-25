import os
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv("TRAVEL_PAYOUTS_API_TOKEN")
if not TOKEN:
    raise ValueError("Missing TRAVEL_PAYOUTS_API_TOKEN in environment")

url = "https://api.travelpayouts.com/v2/prices/latest"
params = {"origin": "LON", "destination": "NYC", "token": TOKEN}  # add chat params here

s = requests.Session()
s.mount("https://", HTTPAdapter(max_retries=Retry(
    total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504]
)))

try:
    r = s.get(url, params=params, timeout=10)
    r.raise_for_status()
    print(r.json())
except requests.exceptions.RequestException as e:
    print("Network problem:", e)
