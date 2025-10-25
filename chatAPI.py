import os
from dotenv import load_dotenv
import openai

# Load environment variables from .env
load_dotenv()

# Get the API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Missing OPENAI_API_KEY in environment or .env file")




# CHAT with user 
client_front = openai.OpenAI(api_key=api_key)

response_front = client_front.responses.create(
    model="gpt-5",
    input="say red." # input flight api response here
)

print(response_front.output_text)






# CHAT with flights
client_back = openai.OpenAI(api_key=api_key)

response_back = client_back.responses.create(
    model="gpt-5",
    input="say blue." # input flight api response here
)

print(response_back.output_text)