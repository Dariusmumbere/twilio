import json
import google.generativeai as genai
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from twilio.twiml.messaging_response import MessagingResponse

# Load your personal data
with open("mumbere_darius_profile.json", "r") as file:
    personal_data = json.load(file)

# Twilio Credentials
TWILIO_ACCOUNT_SID = "AC4ba7ceaed874c35acd3b1f5dbc880ba9"
TWILIO_AUTH_TOKEN = "03f57b5fae10b0e378c9564fb394f14d"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"

# Directly set your API key here
api_key = "AIzaSyAN23PVrXsIBkYO43JVrXa69hdbRvBqkoY"  # Replace with your actual key

# Configure Gemini API
genai.configure(api_key=api_key)

# Initialize conversation history
conversation_history = []

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def send_whatsapp_message(to, message):
    """Send a WhatsApp message using Twilio."""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    data = {
        "From": TWILIO_WHATSAPP_NUMBER,
        "To": to,
        "Body": message
    }
    response = requests.post(url, data=data, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
    return response.json()

# Flask API
app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

@app.route("/ask", methods=["POST"])
def ask_question():
    """Handle chatbot queries from the web app."""
    user_question = request.json.get("question")
    if not user_question:
        return jsonify({"error": "No question provided"}), 400

    answer = ask_gemini(user_question, conversation_history)

    # Update conversation history
    conversation_history.append({"user": user_question, "ai": answer})
    if len(conversation_history) > 5:  # Keep the last 5 exchanges
        conversation_history.pop(0)

    return jsonify({"answer": answer})

@app.route("/whatsapp-webhook", methods=["POST"])
def whatsapp_webhook():
    """Receive WhatsApp messages and respond using the chatbot."""
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")

    if not incoming_msg:
        return "No message received", 400

    # Get AI response
    ai_response = ask_gemini(incoming_msg, conversation_history)

    # Create Twilio response (instead of sending manually)
    twilio_response = MessagingResponse()
    twilio_response.message(ai_response)

    return str(twilio_response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
