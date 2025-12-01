"""
Flask web UI for the Graph RAG system.
Acts as a thin frontend that calls the RAG API over HTTP.
"""

import os

import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)

# RAG API base URL (inside cluster: http://rag-api:8000, local dev: http://localhost:8000)
RAG_API_URL = os.getenv("RAG_API_URL", "http://rag-api:8000")

# Register blueprints
from services.web_ui.src.routes.upload import upload_bp  # noqa: E402
from services.web_ui.src.routes.admin import admin_bp  # noqa: E402

app.register_blueprint(upload_bp)
app.register_blueprint(admin_bp)


@app.route("/")
def index():
    """Render the main chat page."""
    return render_template("chat.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle chat messages from the frontend by calling the RAG API."""
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    try:
        resp = requests.post(
            f"{RAG_API_URL}/api/v1/chat",
            json={"message": user_message},
            timeout=60,
        )
        resp.raise_for_status()
        payload = resp.json()
        return jsonify(payload), resp.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "web-ui"})


if __name__ == "__main__":
    print("Starting Graph RAG Web UI...")
    print(f"RAG API URL: {RAG_API_URL}")
    app.run(host="0.0.0.0", port=5000, debug=True)
