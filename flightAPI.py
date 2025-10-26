# flightAPI.py
from flight_tools import run_tool_conversation

def main():
    print("✈️  Flight Price Checker CLI")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break

        try:
            response = run_tool_conversation(user_input)
            print(f"AI: {response}\n")
        except Exception as e:
            print(f"[Error] {e}\n")


if __name__ == "__main__":
    main()
