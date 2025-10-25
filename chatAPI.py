import os
from dotenv import load_dotenv
import openai

# Load environment variables from .env
load_dotenv()

# Get the API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Missing OPENAI_API_KEY in environment or .env file")




# CHAT with user from HTML
client_front = openai.OpenAI(api_key=api_key)


# STEP 1
response_front = client_front.responses.create(
    model="gpt-5",
    input="I want to go from Dubai to London" # input user params here
)

# STEP 4 (not needed for flight info, needed to continue chat)
print(response_front.output_text)  # put this in the end 






# CHAT with flight API
client_back = openai.OpenAI(api_key=api_key)


# STEP 2
response_back = client_back.responses.create(
    model="gpt-5",
    input="say blue." # input flight api response here
)


# STEP 3
print(response_back.output_text)



how do i make it so that the user enters something and it goes to the openai so that it can single out the parameters and enter those in the flight api so that we can get the data from the flight api and then send that back to the user (either through openai so that it is formatted right or directly if we can format it without openai)


openai api file 

import os
from dotenv import load_dotenv
import openai

# Load environment variables from .env
load_dotenv()

# Get the API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Missing OPENAI_API_KEY in environment or .env file")




# CHAT with user from HTML
client_front = openai.OpenAI(api_key=api_key)


# STEP 1
response_front = client_front.responses.create(
    model="gpt-5",
    input="I want to go from Dubai to London" # input user params here
)

# STEP 4 (not needed for flight info, needed to continue chat)
print(response_front.output_text)  # put this in the end 






# CHAT with flight API
client_back = openai.OpenAI(api_key=api_key)


# STEP 2
response_back = client_back.responses.create(
    model="gpt-5",
    input="say blue." # input flight api response here
)


# STEP 3
print(response_back.output_text)





flight api File

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
