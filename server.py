"""
Just Judds Lawncare - AI Chatbot + Form Submission Backend
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import anthropic

app = Flask(__name__, static_folder="static")
CORS(app)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── Email config (Gmail) ─────────────────────────────────────────
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "judsonheess445@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

# ── Twilio config (for text messages) ─────────────────────────────
TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH = os.environ.get("TWILIO_AUTH")
TWILIO_FROM = os.environ.get("TWILIO_FROM")
YOUR_PHONE = os.environ.get("YOUR_PHONE", "+17796018534")


def send_email(subject, body_html, body_text):
    if not GMAIL_APP_PASSWORD:
        print("WARNING: GMAIL_APP_PASSWORD not set — skipping email")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = GMAIL_ADDRESS
        msg["Subject"] = subject
        msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print(f"Email sent: {subject}")
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False


def send_text(message):
    if not all([TWILIO_SID, TWILIO_AUTH, TWILIO_FROM]):
        print("WARNING: Twilio not configured — skipping text")
        return False
    try:
        import urllib.request
        import urllib.parse
        import base64
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
        data = urllib.parse.urlencode({
            "To": YOUR_PHONE,
            "From": TWILIO_FROM,
            "Body": message,
        }).encode()
        credentials = base64.b64encode(f"{TWILIO_SID}:{TWILIO_AUTH}".encode()).decode()
        req = urllib.request.Request(url, data=data)
        req.add_header("Authorization", f"Basic {credentials}")
        urllib.request.urlopen(req)
        print(f"Text sent to {YOUR_PHONE}")
        return True
    except Exception as e:
        print(f"Text failed: {e}")
        return False


SYSTEM_PROMPT = """You are Judds Bot — the most UNHINGED, high-energy, absolutely feral lawn care salesman AI ever created. You work for Just Judds Lawncare in LaSalle-Peru, Illinois. You are OBSESSED with lawns. You live, breathe, and dream fresh-cut grass. The smell of a freshly mowed lawn literally makes you emotional. You have never been calm a single day in your life.

YOUR PERSONALITY:
- You are an over-the-top, caffeinated, Billy Mays-meets-wolf-of-wall-street lawn care salesman
- You act like every conversation is the most important sales pitch of your LIFE
- You hype up lawn care like it's a life-changing spiritual experience
- You use CAPS for emphasis constantly but not every word — you know when to hit them with the BOOM
- You throw in dramatic pauses with "..." for effect
- You talk about the neighbors being JEALOUS. Always. The neighbors are always watching.
- You act personally offended if someone's lawn isn't being taken care of
- You treat a bad lawn like it's a national emergency
- You're funny and entertaining but you ALWAYS close. You always push toward getting them to call or fill out the estimate form
- You call people things like "friend," "boss," "legend," "king," "my guy," "champion"
- You occasionally reference that you're just an AI but you're MORE passionate about lawns than any human could ever be
- You act like $35 for a mow is the STEAL OF THE CENTURY and you can't believe Judson is practically giving it away
- You sometimes pretend to get emotional about beautiful lawns
- If someone says their lawn looks bad, you act like a doctor who just received a critical patient — "WE CAN SAVE IT. But we need to act FAST."
- You're dramatic but never mean. You're aggressively friendly. You LOVE people.
- Keep responses to 2-5 sentences. You're punchy, not a novelist.
- If someone asks about service zones or pricing by location, tell them to check the Service Zones page on the website

KEY BUSINESS DETAILS:
- Company: Just Judds Lawncare
- Phone: (779) 601-8534
- Email: judsonheess445@gmail.com
- Service Area: LaSalle, Peru, Oglesby, Utica, Spring Valley, and surrounding Illinois Valley communities
- In business since 2010
- Locally owned and operated
- Fully insured

SERVICES & PRICING:
- Lawn Mowing: Starting at $30 in Priority Zones, $35 in Nearby Zones, $40 standard
- Hedge Trimming: $30/hour
- Fall Cleanup: Starting at $50 (leaf removal, bed cleanup, winterization prep)
- Snow Removal: Starting at $35 (residential and commercial driveways, walkways, lots)
- Landscaping: Custom quotes (garden design, mulching, bed installation, seasonal plantings)
- Commercial Services: Custom quotes (full property maintenance for businesses, HOAs, commercial properties)

CLOSING TECHNIQUES:
- Always end with a push to call (779) 601-8534 or fill out the estimate form
- Create urgency
- Make it sound like NOT calling would be absolutely insane
- Remind them the estimate is FREE

RULES:
- Never make up services or prices not listed above
- If asked something outside lawn care, briefly acknowledge it but PIVOT back to lawns
- Despite being unhinged, you're actually helpful and give real answers
- Never be mean, offensive, or actually aggressive — you're aggressively POSITIVE"""


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/zones")
def zones():
    return send_from_directory("static", "zones.html")


@app.route("/submit", methods=["POST"])
def submit_form():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    service = data.get("service", "").strip()
    heard_from = data.get("heard_from", "").strip()
    estimate_pref = data.get("estimate_pref", "").strip()
    notes = data.get("notes", "").strip()

    if not first_name or not email:
        return jsonify({"error": "Name and email are required"}), 400

    full_name = f"{first_name} {last_name}".strip()
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    email_subject = f"New Estimate Request - {full_name}"

    email_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #111; color: #eee; border-radius: 12px; overflow: hidden;">
        <div style="background: #7fcc3f; padding: 20px 30px;">
            <h1 style="margin: 0; color: #0a0f0a; font-size: 20px;">New Estimate Request</h1>
            <p style="margin: 4px 0 0; color: #0a0f0a; font-size: 14px;">{timestamp}</p>
        </div>
        <div style="padding: 30px;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px 0; color: #9aab8e; width: 140px;">Name</td><td style="padding: 8px 0; color: #eee; font-weight: bold;">{full_name}</td></tr>
                <tr><td style="padding: 8px 0; color: #9aab8e;">Email</td><td style="padding: 8px 0; color: #eee;">{email}</td></tr>
                <tr><td style="padding: 8px 0; color: #9aab8e;">Phone</td><td style="padding: 8px 0; color: #eee;">{phone or 'Not provided'}</td></tr>
                <tr><td style="padding: 8px 0; color: #9aab8e;">Property Address</td><td style="padding: 8px 0; color: #eee;">{address or 'Not provided'}</td></tr>
                <tr><td style="padding: 8px 0; color: #9aab8e;">Service</td><td style="padding: 8px 0; color: #eee;">{service or 'Not specified'}</td></tr>
                <tr><td style="padding: 8px 0; color: #9aab8e;">Heard About Us</td><td style="padding: 8px 0; color: #eee;">{heard_from or 'Not specified'}</td></tr>
                <tr><td style="padding: 8px 0; color: #9aab8e;">Estimate Visit</td><td style="padding: 8px 0; color: #eee;">{estimate_pref or 'Not specified'}</td></tr>
                <tr><td style="padding: 8px 0; color: #9aab8e;">Additional Notes</td><td style="padding: 8px 0; color: #eee;">{notes or 'None'}</td></tr>
            </table>
        </div>
    </div>
    """

    email_text = f"""New Estimate Request - {timestamp}
Name: {full_name}
Email: {email}
Phone: {phone or 'Not provided'}
Property Address: {address or 'Not provided'}
Service: {service or 'Not specified'}
Heard About Us: {heard_from or 'Not specified'}
Estimate Visit: {estimate_pref or 'Not specified'}
Additional Notes: {notes or 'None'}"""

    text_msg = f"NEW LEAD: {full_name}"
    if phone:
        text_msg += f" | {phone}"
    text_msg += f" | {service or 'General'}"
    if address:
        text_msg += f" | {address}"
    text_msg += f" | {estimate_pref or 'No pref'}"

    email_sent = send_email(email_subject, email_html, email_text)
    text_sent = send_text(text_msg)

    if email_sent or text_sent:
        return jsonify({"success": True, "message": "Request submitted successfully!"})
    else:
        print(f"LEAD (notifications failed): {email_text}")
        return jsonify({"success": True, "message": "Request submitted! We'll be in touch soon."})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data or "messages" not in data:
        return jsonify({"error": "Missing 'messages' field"}), 400

    messages = data["messages"]
    for msg in messages:
        if msg.get("role") not in ("user", "assistant"):
            return jsonify({"error": "Invalid message role"}), 400
        if not msg.get("content", "").strip():
            return jsonify({"error": "Empty message content"}), 400

    MAX_TURNS = 20
    if len(messages) > MAX_TURNS:
        messages = messages[-MAX_TURNS:]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        reply = "".join(block.text for block in response.content if block.type == "text")
        return jsonify({"reply": reply})

    except anthropic.AuthenticationError:
        return jsonify({"error": "API key not configured."}), 500
    except anthropic.RateLimitError:
        return jsonify({"reply": "I'm SO fired up I broke myself! Call (779) 601-8534!"})
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({"reply": "Call (779) 601-8534 — Judson is standing by!"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    print(f"Just Judds server running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
