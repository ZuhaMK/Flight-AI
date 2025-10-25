import os
import requests
import json
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import openai

# --- 0. Initialization ---
# Load environment variables from .env
load_dotenv()

# Get the API keys
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Missing OPENAI_API_KEY in environment or .env file")

client = openai.OpenAI(api_key=api_key)

# --- 1. Define the Tool (Python Function) ---

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
    TOKEN = os.getenv("TRAVEL_PAYOUTS_API_TOKEN")
    if not TOKEN:
        return json.dumps({"error": "Missing API token for flight service."})

    url = "https://api.travelpayouts.com/v2/prices/latest"
    params = {
        "origin": origin, 
        "destination": destination, 
        "token": TOKEN
        # 'depart_date': date, # Uncomment and use if your API supports date
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

# A mapping of available functions
available_tools = {
    "get_flight_prices": get_flight_prices,
}

# --- 2. Define the Tool Schema for the LLM ---

tool_schema = {
    "type": "function",
    "function": {
        "name": "get_flight_prices",
        "description": "Get current flight prices between two cities. Requires IATA codes for origin and destination.",
        "parameters": {
            "type": "object",
            "properties": {
                "origin": {
                    "type": "string",
                    "description": "The IATA code for the departure city, e.g., 'DXB' for Dubai.",
                },
                "destination": {
                    "type": "string",
                    "description": "The IATA code for the arrival city, e.g., 'LON' for London.",
                },
            },
            "required": ["origin", "destination"],
        },
    }
}

# --- 3. The Conversation Orchestrator ---

def run_conversation(user_prompt: str):
    
    # 3.1: Start the conversation with the user's prompt and tool definition
    messages = [{"role": "user", "content": user_prompt}]
    
    response = client.chat.completions.create(
        model="gpt-4-turbo", 
        messages=messages,
        tools=[tool_schema],
        tool_choice="auto",
    )

    response_message = response.choices[0].message
    
    # 3.2: Check if the LLM requested a function call
    if response_message.tool_calls:
        tool_calls = response_message.tool_calls
        
        # Add the LLM's function call request to the history
        messages.append(response_message)
        
        # Execute the function call
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_tools.get(function_name)
            
            # The LLM returns arguments as a JSON string, so we parse it
            function_args = json.loads(tool_call.function.arguments)

            if function_to_call:
                print(f"[LOG] Calling function: {function_name} with args: {function_args}")
                
                # Execute the actual Python function
                function_response = function_to_call(
                    origin=function_args.get("origin"),
                    destination=function_args.get("destination"),
                )
                
                # 3.3: Send the function's result (flight data) back to the LLM
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response, # Raw JSON data
                    }
                )

        # 3.4: Get the final, formatted response
        print("[LOG] Sending flight data back to LLM for final formatting...")
        final_response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages, # Full history with tool result
        )
        return final_response.choices[0].message.content
        
    else:
        # 3.5: If no tool was called (e.g., a simple greeting)
        return response_message.content

# --- 4. Example Execution ---

user_input = "Can you check the flight prices from Dubai to London?" 
print(f"User Input: {user_input}")

final_text_output = run_conversation(user_input)

print("\n--- Final User Response ---")
print(final_text_output)