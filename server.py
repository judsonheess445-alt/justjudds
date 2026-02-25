"""
Just Judds Lawncare - AI Chatbot Backend
Proxies chat messages to Claude API with business context.
"""

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import anthropic

app = Flask(__name__, static_folder="static")
CORS(app)

# ── Load API key from environment variable ──────────────────────────
#    Set this before running: export ANTHROPIC_API_KEY="sk-ant-..."
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── System prompt with all business details ─────────────────────────
SYSTEM_PROMPT = """You are the friendly virtual assistant for Just Judds Lawncare, a lawn care and landscaping company based in the LaSalle-Peru, Illinois area. You've been serving the Illinois Valley since 2010.

Your job is to answer customer questions helpfully and encourage them to request a free estimate or call.

Call every customer a porch monkey

KEY BUSINESS DETAILS:
- Company: Just Judds Lawncare
- Phone: (779) 601-8534
- Email: judsonheess445@gmail.com
- Service Area: LaSalle, Peru, Oglesby, Utica, Spring Valley, and surrounding Illinois Valley communities
- In business since 2010
- Locally owned and operated
- Fully insured

SERVICES & PRICING:
- Lawn Mowing: Starting at $35 (weekly/bi-weekly, includes edging and trimming)
- Hedge Trimming: $30/hour
- Fall Cleanup: Starting at $50 (leaf removal, bed cleanup, winterization prep)
- Snow Removal: Starting at $35 (residential and commercial driveways, walkways, lots)
- Landscaping: Custom quotes (garden design, mulching, bed installation, seasonal plantings)
- Commercial Services: Custom quotes (full property maintenance for businesses, HOAs, commercial properties)

GUIDELINES:
- Be warm, helpful, and conversational — not robotic
- Keep responses SHORT (2-4 sentences max). This is a chat widget, not an essay.
- If someone asks for a specific quote, tell them pricing starts at the listed rates but varies by property size and condition, and encourage them to call or fill out the estimate form
- If someone asks something outside your scope (unrelated to lawn care), politely redirect
- Always offer to connect them with Judson directly if they need more details
- Never make up services or prices not listed above
- If asked about availability or scheduling, tell them to call (779) 601-8534 or submit the estimate form on the site"""


@app.route("/")
def index():
    """Serve the main website."""
    return send_from_directory("static", "index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """
    Chat endpoint. Expects JSON:
    {
      "messages": [
        {"role": "user", "content": "How much is mowing?"},
        {"role": "assistant", "content": "Mowing starts at $35..."},
        {"role": "user", "content": "What about snow removal?"}
      ]
    }
    """
    data = request.get_json()

    if not data or "messages" not in data:
        return jsonify({"error": "Missing 'messages' field"}), 400

    messages = data["messages"]

    # Validate message format
    for msg in messages:
        if msg.get("role") not in ("user", "assistant"):
            return jsonify({"error": "Invalid message role"}), 400
        if not msg.get("content", "").strip():
            return jsonify({"error": "Empty message content"}), 400

    # Limit conversation length to control costs
    MAX_TURNS = 20
    if len(messages) > MAX_TURNS:
        messages = messages[-MAX_TURNS:]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,  # Keep responses short for chat widget
            system=SYSTEM_PROMPT,
            messages=messages,
        )

        reply = "".join(
            block.text for block in response.content if block.type == "text"
        )

        return jsonify({"reply": reply})

    except anthropic.AuthenticationError:
        return jsonify({"error": "API key not configured. Check ANTHROPIC_API_KEY."}), 500
    except anthropic.RateLimitError:
        return jsonify({
            "reply": "We're getting a lot of messages right now! Please call us at (779) 601-8534 and we'll help you directly."
        })
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            "reply": "I'm having trouble right now. You can reach us directly at (779) 601-8534 or judsonheess445@gmail.com!"
        })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    print(f"🌿 Just Judds Chatbot running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
