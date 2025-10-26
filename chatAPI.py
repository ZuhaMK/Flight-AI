# app.py
import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from flight_tools import run_tool_conversation  # ✅ Import shared logic

# -------------------------------------------------------------
# 1. Flask Initialization
# -------------------------------------------------------------
load_dotenv()

app = Flask(__name__, template_folder="Web")
CORS(app)  # ✅ Allows requests from local HTML files (optional but useful)

# -------------------------------------------------------------
# 2. Chat Endpoint (Used by Frontend JS)
# -------------------------------------------------------------
@app.route("/chat", methods=["POST"])
def chat():
    """Handles chat messages from the frontend."""
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Please enter a message."})

    print(f"[USER] {user_message}")
    try:
        reply = run_tool_conversation(user_message)
        print(f"[AI] {reply}")
        return jsonify({"reply": reply})
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"reply": f"Error: {e}"}), 500


# -------------------------------------------------------------
# 3. Root Route (Serves Your Web UI)
# -------------------------------------------------------------
@app.route("/")
def home():
    """Serves the main HTML page (Web/Main.html)."""
    return render_template("Main.html")


# -------------------------------------------------------------
# 4. Run Server
# -------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Flask server running on http://127.0.0.1:5000/")
    app.run(debug=True, port=5000)
