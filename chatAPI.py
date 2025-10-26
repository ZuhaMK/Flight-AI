# app.py (The Flask Server)
import os
import requests
import json
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from flask import Flask, request, jsonify, render_template  # <<< FLASK IS HERE NOW
from openai import OpenAI

# Load environment variables (from .env)
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Missing OPENAI_API_KEY in environment or .env file")

app = Flask(__name__,template_folder='Web')
client = OpenAI(api_key=api_key)


# -------------------------------------------------------------
# 1. DEFINE THE TOOL (PYTHON FUNCTION) AND MAPPING
# -------------------------------------------------------------

def get_flight_prices(origin: str, destination: str, date: str = None) -> str:
    """ Calls the Travel Payouts API to get flight prices. """
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


available_tools = {"get_flight_prices": get_flight_prices}

# -------------------------------------------------------------
# 2. DEFINE THE TOOL SCHEMA
# -------------------------------------------------------------

tool_schema = {
    "type": "function",
    "function": {
        "name": "get_flight_prices",
        "description": "Get current flight prices between two cities. Requires IATA codes for origin and destination.",
        "parameters": {
            "type": "object",
            "properties": {
                "origin": {"type": "string",
                           "description": "The IATA code for the departure city, e.g., 'DXB' for Dubai."},
                "destination": {"type": "string",
                                "description": "The IATA code for the arrival city, e.g., 'LON' for London."},
            },
            "required": ["origin", "destination"],
        },
    }
}


# -------------------------------------------------------------
# 3. TOOL-CALLING ORCHESTRATOR
# -------------------------------------------------------------

def run_tool_conversation(user_prompt: str) -> str:
    # Full logic from the previous step is now inside this function
    messages = [{"role": "user", "content": user_prompt}]

    # ... (Rest of the run_conversation logic) ...
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        tools=[tool_schema],
        tool_choice="auto",
    )

    response_message = response.choices[0].message

    if response_message.tool_calls:
        tool_calls = response_message.tool_calls
        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_tools.get(function_name)
            function_args = json.loads(tool_call.function.arguments)

            if function_to_call:
                print(f"[LOG] Calling function: {function_name} with args: {function_args}")
                function_response = function_to_call(**function_args)

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })

        final_response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
        )
        return final_response.choices[0].message.content

    else:
        return response_message.content


# -------------------------------------------------------------
# 4. FLASK ROUTE (The API Endpoint)
# -------------------------------------------------------------

@app.route("/chat", methods=["POST"])
def chat():
    """ Handles the chat request from the JS frontend. """
    user_message = request.json["message"]

    # This is the single function call that runs the whole process
    reply = run_tool_conversation(user_message)

    return jsonify({"reply": reply})


# This is the default route that serves your HTML file.
# You must create an 'index.html' file for this to work.
@app.route("/")
def home():
    """ Serves the main HTML page. """
    # In a real app, you'd use render_template('index.html')
    # but for simplicity here, assume the HTML file is opened directly
    # OR you can use Flask to serve it:
    # return app.send_static_file('index.html')
    # For now, just confirming the app is running:
    return render_template('Main.html')


if __name__ == "__main__":
    app.run(debug=True, port=5000)