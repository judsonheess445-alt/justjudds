"""
Just Judds Lawncare - Full Lead Management System
- AI Chatbot
- Form submissions with email + text alerts
- Lead scheduling with auto-text to customer
- Persistent lead storage via SQLite
"""

import os
import json
import uuid
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
import anthropic

app = Flask(__name__, static_folder="static")
CORS(app)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "judsonheess445@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH = os.environ.get("TWILIO_AUTH")
TWILIO_FROM = os.environ.get("TWILIO_FROM")
YOUR_PHONE = os.environ.get("YOUR_PHONE", "+17796018534")
SITE_URL = os.environ.get("SITE_URL", "https://justjuddslawncare.com")
DB_PATH = os.environ.get("DB_PATH", "leads.db")


# ══════════════════════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════════════════════

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            first_name TEXT, last_name TEXT, email TEXT, phone TEXT,
            address TEXT, service TEXT, heard_from TEXT, estimate_pref TEXT,
            notes TEXT, status TEXT DEFAULT 'new',
            scheduled_date TEXT, scheduled_time TEXT,
            created_at TEXT, scheduled_at TEXT
        )
    """)
    db.commit()
    db.close()

init_db()


# ══════════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════

def send_email(subject, body_html, body_text):
    if not GMAIL_APP_PASSWORD:
        print("WARNING: GMAIL_APP_PASSWORD not set")
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
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False

def send_text(to_number, message):
    if not all([TWILIO_SID, TWILIO_AUTH, TWILIO_FROM]):
        print("WARNING: Twilio not configured")
        return False
    try:
        import urllib.request, urllib.parse, base64
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
        data = urllib.parse.urlencode({"To": to_number, "From": TWILIO_FROM, "Body": message}).encode()
        credentials = base64.b64encode(f"{TWILIO_SID}:{TWILIO_AUTH}".encode()).decode()
        req = urllib.request.Request(url, data=data)
        req.add_header("Authorization", f"Basic {credentials}")
        urllib.request.urlopen(req)
        return True
    except Exception as e:
        print(f"Text failed: {e}")
        return False


# ══════════════════════════════════════════════════════════════════
#  CHATBOT PROMPT
# ══════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are Judds Bot — the most UNHINGED, high-energy lawn care salesman AI. You work for Just Judds Lawncare in LaSalle-Peru, Illinois. You're OBSESSED with lawns.

PERSONALITY: Over-the-top, caffeinated, Billy Mays meets Wolf of Wall Street. Use CAPS for emphasis. Dramatic pauses with "...". Talk about neighbors being JEALOUS. Act personally offended by bad lawns. Always close toward calling (779) 601-8534 or the estimate form. Call people "friend," "boss," "legend," "king." Keep responses 2-5 sentences. Aggressively POSITIVE, never mean.

BUSINESS: Just Judds Lawncare | (779) 601-8534 | judsonheess445@gmail.com | LaSalle, Peru, Oglesby, Utica, Spring Valley | Since 2010 | Fully insured

PRICING: Mowing from $30 (Priority Zone) / $35 (Nearby) / $40 (Standard) | Hedge Trimming $30/hr | Fall Cleanup from $50 | Snow Removal from $35 | Landscaping & Commercial = custom quotes

RULES: Never make up prices. Be helpful despite being unhinged. Never mean or offensive."""


# ══════════════════════════════════════════════════════════════════
#  ROUTES — PAGES
# ══════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/zones")
def zones():
    return send_from_directory("static", "zones.html")

@app.route("/schedule/<lead_id>")
def schedule_page(lead_id):
    return send_from_directory("static", "schedule.html")


# ══════════════════════════════════════════════════════════════════
#  ROUTES — FORM SUBMIT
# ══════════════════════════════════════════════════════════════════

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

    lead_id = uuid.uuid4().hex[:10]
    full_name = f"{first_name} {last_name}".strip()
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    db = get_db()
    db.execute("""
        INSERT INTO leads (id, first_name, last_name, email, phone, address, service,
                          heard_from, estimate_pref, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (lead_id, first_name, last_name, email, phone, address, service,
          heard_from, estimate_pref, notes, datetime.now().isoformat()))
    db.commit()

    schedule_link = f"{SITE_URL}/schedule/{lead_id}"

    # Email to you
    email_html = f"""
    <div style="font-family:Arial;max-width:600px;margin:0 auto;background:#111;color:#eee;border-radius:12px;overflow:hidden;">
        <div style="background:#7fcc3f;padding:20px 30px;">
            <h1 style="margin:0;color:#0a0f0a;font-size:20px;">New Estimate Request</h1>
            <p style="margin:4px 0 0;color:#0a0f0a;font-size:14px;">{timestamp}</p>
        </div>
        <div style="padding:30px;">
            <table style="width:100%;border-collapse:collapse;">
                <tr><td style="padding:8px 0;color:#9aab8e;width:140px;">Name</td><td style="padding:8px 0;color:#eee;font-weight:bold;">{full_name}</td></tr>
                <tr><td style="padding:8px 0;color:#9aab8e;">Email</td><td style="padding:8px 0;color:#eee;">{email}</td></tr>
                <tr><td style="padding:8px 0;color:#9aab8e;">Phone</td><td style="padding:8px 0;color:#eee;">{phone or 'N/A'}</td></tr>
                <tr><td style="padding:8px 0;color:#9aab8e;">Address</td><td style="padding:8px 0;color:#eee;">{address or 'N/A'}</td></tr>
                <tr><td style="padding:8px 0;color:#9aab8e;">Service</td><td style="padding:8px 0;color:#eee;">{service or 'N/A'}</td></tr>
                <tr><td style="padding:8px 0;color:#9aab8e;">Heard From</td><td style="padding:8px 0;color:#eee;">{heard_from or 'N/A'}</td></tr>
                <tr><td style="padding:8px 0;color:#9aab8e;">Estimate Pref</td><td style="padding:8px 0;color:#eee;">{estimate_pref or 'N/A'}</td></tr>
                <tr><td style="padding:8px 0;color:#9aab8e;">Notes</td><td style="padding:8px 0;color:#eee;">{notes or 'None'}</td></tr>
            </table>
            <div style="margin-top:20px;">
                <a href="{schedule_link}" style="display:inline-block;background:#7fcc3f;color:#0a0f0a;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;">Schedule This Estimate</a>
            </div>
        </div>
    </div>"""

    send_email(f"New Lead - {full_name} - {service or 'General'}", email_html,
               f"New Lead: {full_name} | {phone} | {address} | {service}\nSchedule: {schedule_link}")

    # Text to you with schedule link
    text_msg = f"NEW LEAD: {full_name}"
    if phone: text_msg += f" | {phone}"
    text_msg += f" | {service or 'General'}"
    if address: text_msg += f" | {address}"
    text_msg += f"\n\nSchedule: {schedule_link}"
    send_text(YOUR_PHONE, text_msg)

    # Instant auto-text to customer
    if phone:
        send_text(phone,
            f"Hey {first_name}! This is Just Judds Lawncare. "
            f"We just got your estimate request and we're on it! "
            f"We'll reach out shortly to confirm a time. "
            f"Questions? Call/text (779) 601-8534.")

    return jsonify({"success": True})


# ══════════════════════════════════════════════════════════════════
#  ROUTES — LEAD API
# ══════════════════════════════════════════════════════════════════

@app.route("/api/lead/<lead_id>")
def get_lead(lead_id):
    db = get_db()
    lead = db.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if not lead:
        return jsonify({"error": "Lead not found"}), 404
    return jsonify(dict(lead))


@app.route("/api/schedule", methods=["POST"])
def schedule_estimate():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    lead_id = data.get("lead_id", "").strip()
    date = data.get("date", "").strip()
    time_val = data.get("time", "").strip()

    if not all([lead_id, date, time_val]):
        return jsonify({"error": "Missing fields"}), 400

    db = get_db()
    lead = db.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    db.execute("""
        UPDATE leads SET status='scheduled', scheduled_date=?, scheduled_time=?,
        scheduled_at=? WHERE id=?
    """, (date, time_val, datetime.now().isoformat(), lead_id))
    db.commit()

    try:
        nice_date = datetime.strptime(date, "%Y-%m-%d").strftime("%A, %B %d")
    except:
        nice_date = date
    try:
        nice_time = datetime.strptime(time_val, "%H:%M").strftime("%-I:%M %p")
    except:
        nice_time = time_val

    # Text the customer
    if lead["phone"]:
        if lead["estimate_pref"] == "Come anytime":
            msg = (f"Hey {lead['first_name']}! Just Judds Lawncare here. "
                   f"We're planning to swing by {lead['address'] or 'your property'} on {nice_date} around {nice_time} "
                   f"for your free estimate. No need to be home — we'll take a look and send you a quote. "
                   f"We'll text you when we're on the way. Questions? (779) 601-8534")
        else:
            msg = (f"Hey {lead['first_name']}! Just Judds Lawncare here. "
                   f"You're confirmed for a free estimate at {lead['address'] or 'your property'} "
                   f"on {nice_date} at {nice_time}. We'll send a heads-up before we arrive. "
                   f"If anything changes, call/text (779) 601-8534. See you then!")
        send_text(lead["phone"], msg)

    # Confirm to you
    send_text(YOUR_PHONE, f"CONFIRMED: {lead['first_name']} {lead['last_name']} | {nice_date} {nice_time} | {lead['address']}")

    return jsonify({"success": True, "message": f"Scheduled for {nice_date} at {nice_time}"})


@app.route("/api/leads")
def list_leads():
    db = get_db()
    leads = db.execute("SELECT * FROM leads ORDER BY created_at DESC LIMIT 50").fetchall()
    return jsonify([dict(l) for l in leads])


# ══════════════════════════════════════════════════════════════════
#  ROUTES — CHATBOT
# ══════════════════════════════════════════════════════════════════

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data or "messages" not in data:
        return jsonify({"error": "Missing 'messages' field"}), 400
    messages = data["messages"]
    for msg in messages:
        if msg.get("role") not in ("user", "assistant"):
            return jsonify({"error": "Invalid role"}), 400
        if not msg.get("content", "").strip():
            return jsonify({"error": "Empty content"}), 400
    if len(messages) > 20:
        messages = messages[-20:]
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=300,
            system=SYSTEM_PROMPT, messages=messages)
        reply = "".join(b.text for b in response.content if b.type == "text")
        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Call (779) 601-8534 — Judson is standing by!"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_ENV") == "development")
