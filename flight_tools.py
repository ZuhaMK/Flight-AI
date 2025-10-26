# flight_tools.py
import os
import json
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from openai import OpenAI

# --- Load environment variables ---
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Missing OPENAI_API_KEY in environment or .env file")

client = OpenAI(api_key=api_key)

# --- 1. Define the Flight Tool ---
def get_flight_prices(origin: str, destination: str, date: str = None) -> str:
    """Calls the Travel Payouts API to get flight prices."""
    TOKEN = os.getenv("TRAVEL_PAYOUTS_API_TOKEN")
    if not TOKEN:
        return json.dumps({"error": "Missing API token for flight service."})

    url = "https://api.travelpayouts.com/v2/prices/latest"
    params = {
        "origin": origin,
        "destination": destination,
        "token": TOKEN
    }

    s = requests.Session()
    s.mount("https://", HTTPAdapter(max_retries=Retry(
        total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504]
    )))

    try:
        r = s.get(url, params=params, timeout=10)
        r.raise_for_status()
        return json.dumps(r.json())
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Flight API network problem: {e}"})


# --- 2. Tool Schema ---
tool_schema = {
    "type": "function",
    "function": {
        "name": "get_flight_prices",
        "description": "Get current flight prices between two cities using IATA codes.",
        "parameters": {
            "type": "object",
            "properties": {
                "origin": {
                    "type": "string",
                    "description": "The IATA code for the departure city, e.g., 'DXB' for Dubai."
                },
                "destination": {
                    "type": "string",
                    "description": "The IATA code for the arrival city, e.g., 'LON' for London."
                }
            },
            "required": ["origin", "destination"]
        }
    }
}

available_tools = {"get_flight_prices": get_flight_prices}

# --- 3. Orchestrator Function ---
def run_tool_conversation(user_prompt: str) -> str:
    """Handles the full GPT + tool interaction."""
    messages = [{"role": "user", "content": user_prompt}]

    # Step 1: Ask GPT how to proceed
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        tools=[tool_schema],
        tool_choice="auto"
    )

    response_message = response.choices[0].message

    # Step 2: If GPT calls a tool
    if response_message.tool_calls:
        tool_calls = response_message.tool_calls
        messages.append(response_message)

        for tool_call in tool_calls:
            fn_name = tool_call.function.name
            fn_to_call = available_tools.get(fn_name)
            fn_args = json.loads(tool_call.function.arguments)

            if fn_to_call:
                print(f"[LOG] Calling {fn_name} with args: {fn_args}")
                fn_result = fn_to_call(**fn_args)

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": fn_name,
                    "content": fn_result
                })

        # Step 3: Final GPT message after tool data
        final_response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages
        )
        return final_response.choices[0].message.content

    # Step 4: If GPT responds directly
    return response_message.content
