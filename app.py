import json
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

# Load personal data
with open("mumbere_darius_profile.json", "r") as file:
    personal_data = json.load(file)

# Twilio Credentials (HARD-CODED)
TWILIO_ACCOUNT_SID = "AC4ba7ceaed874c35acd3b1f5dbc880ba9"
TWILIO_AUTH_TOKEN = "[AuthToken]"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"

# Initialize Twilio Client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Google Gemini API Key (HARD-CODED)
API_KEY = "AIzaSyAN23PVrXsIBkYO43JVrXa69hdbRvBqkoY"

# Configure Gemini API
genai.configure(api_key=API_KEY)

# Initialize conversation history
conversation_history = []

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def ask_gemini(prompt, history):
    """Get AI-generated responses from Gemini."""
    try:
        chat = genai.GenerativeModel("gemini-pro").start_chat(history=history)
        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Gemini API error: {str(e)}")
        return "I'm currently facing technical issues. Please try again later."

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

    # Send response via Twilio
    message = twilio_client.messages.create(
        body=ai_response,
        from_=TWILIO_WHATSAPP_NUMBER,
        to=sender
    )

    logging.info(f"Sent message to {sender}: {ai_response}")
    return "Message sent", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
