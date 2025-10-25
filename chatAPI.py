import os
from dotenv import load_dotenv
import openai
import json # Import for JSON handling

# Load environment variables from .env
load_dotenv()

# Get the API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Missing OPENAI_API_KEY in environment or .env file")

client = openai.OpenAI(api_key=api_key)

# --- Define the tool/function schema for the LLM ---

# This describes the Python function get_flight_prices to the LLM
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
                # You can add 'date' here too if your API supports it and you 
                # want the LLM to extract it.
            },
            "required": ["origin", "destination"],
        },
    }
}

# Assume get_flight_prices and available_tools are defined as in Section 1

def run_conversation(user_prompt: str):
    # STEP 1: Send the user input and the tool definition to the LLM
    messages = [{"role": "user", "content": user_prompt}]
    
    response = client.chat.completions.create(
        model="gpt-4-turbo", # Use a model that supports function calling (e.g., gpt-4-turbo)
        messages=messages,
        tools=[tool_schema],
        tool_choice="auto", # Allows the LLM to decide whether to call the function
    )

    response_message = response.choices[0].message
    
    # STEP 2: Check if the LLM decided to call a function
    if response_message.tool_calls:
        tool_calls = response_message.tool_calls
        
        # Add the LLM's function call request to the conversation history
        messages.append(response_message)
        
        # Execute each function call requested by the LLM
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_tools.get(function_name)
            function_args = json.loads(tool_call.function.arguments)

            if function_to_call:
                print(f"Calling function: {function_name} with args: {function_args}")
                
                # Call the actual Python function with parameters extracted by the LLM
                function_response = function_to_call(
                    origin=function_args.get("origin"),
                    destination=function_args.get("destination"),
                    # Add other parameters if you defined them
                )
                
                # STEP 3: Send the function's response (flight data) back to the LLM
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response, # This is the raw flight data JSON
                    }
                )
            else:
                print(f"Error: Unknown tool {function_name}")
                # Handle unknown tool error if necessary

        # STEP 4: Get the final, formatted response from the LLM
        print("Sending flight data back to LLM for final formatting...")
        final_response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages, # Send the full conversation history including the tool call and result
        )
        return final_response.choices[0].message.content
        
    else:
        # If the LLM didn't call the function (e.g., if the query was "Hello")
        return response_message.content

# --- Example Usage ---
user_input = "I want to go from Dubai (DXB) to London (LON) next month" 
final_text_output = run_conversation(user_input)

print("\n--- Final User Response ---")
print(final_text_output)