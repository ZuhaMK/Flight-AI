# flight_tools.py
import os
import json
import re
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

# --- Global Chat History ---
chat_history = [
    {
        "role": "system",
        "content": (
            "You are a helpful flight assistant that ALWAYS responds in clean markdown bullet points.\n"
            "Each key parameter or data point must start with a dash (-) or emoji bullet (•, ✈️, 💰, 📅, etc.).\n"
            "Never write paragraphs. Never use numbering. Only structured bullets."
        )
    }
]

# --- Formatting Helper ---
def format_as_bullets(text: str) -> str:
    """
    Ensures the text is in clean bullet format.
    Converts lists, key-value pairs, and sentences into consistent markdown bullets.
    """
    if not text:
        return ""

    # Replace double newlines with single newlines
    text = re.sub(r'\n{2,}', '\n', text.strip())

    # If text has colons (key-value pairs), convert to "- key: value"
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Add dash if missing
        if not line.startswith(("-", "•", "✈️", "💰", "📅", "🛬", "🔁", "✅")):
            line = f"- {line}"
        lines.append(line)
    return "\n".join(lines)

# --- Flight Tool (unchanged) ---
def get_flight_prices(origin: str, destination: str, date: str = None) -> str:
    TOKEN = os.getenv("TRAVEL_PAYOUTS_API_TOKEN")
    if not TOKEN:
        return json.dumps({"error": "Missing API token for flight service."})

    url = "https://api.travelpayouts.com/v2/prices/latest"
    params = {"origin": origin, "destination": destination, "token": TOKEN}

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


# --- Tool Schema (unchanged) ---
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


# --- Main Conversation Function ---
def run_tool_conversation(user_prompt: str) -> str:
    """Handles GPT + tool interaction with persistent history and clean bullet formatting."""
    global chat_history

    chat_history.append({"role": "user", "content": user_prompt})

    # Step 1: GPT decides what to do
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=chat_history,
        tools=[tool_schema],
        tool_choice="auto"
    )

    response_message = response.choices[0].message
    chat_history.append(response_message)

    # Step 2: Handle tool calls
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)
            fn_to_call = available_tools.get(fn_name)

            if fn_to_call:
                print(f"[LOG] Calling {fn_name} with args: {fn_args}")
                fn_result = fn_to_call(**fn_args)

                chat_history.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": fn_name,
                    "content": fn_result
                })

        # Step 3: Final response after tool execution
        final_response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=chat_history
        )
        final_message = format_as_bullets(final_response.choices[0].message.content)
        chat_history.append({"role": "assistant", "content": final_message})
        return final_message

    # Step 4: Direct reply (no tool)
    final_message = format_as_bullets(response_message.content)
    chat_history.append({"role": "assistant", "content": final_message})
    return final_message
