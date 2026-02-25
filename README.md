# Just Judds Lawncare — Website + AI Chatbot

A sleek, modern website for Just Judds Lawncare with an AI-powered chatbot that answers customer questions about services, pricing, and service area using Claude.

## Project Structure

```
just-judds-chatbot/
├── server.py          # Flask backend (proxies chat to Claude API)
├── requirements.txt   # Python dependencies
├── Procfile           # For cloud deployment (Render/Railway)
├── .env.example       # Environment variable template
└── static/
    └── index.html     # The full website + chatbot frontend
```

## Quick Start (Local)

### 1. Get an Anthropic API Key

Go to [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) and create a key.

### 2. Set Up the Project

```bash
cd just-judds-chatbot

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"   # Mac/Linux
# set ANTHROPIC_API_KEY=sk-ant-your-key-here      # Windows
```

### 3. Run It

```bash
python server.py
```

Open [http://localhost:5000](http://localhost:5000) — your site is live with the chatbot working.

---

## Deploy to the Internet

### Option A: Render (Recommended — Free Tier)

1. Push this folder to a GitHub repo
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn server:app --bind 0.0.0.0:$PORT`
5. Add environment variable: `ANTHROPIC_API_KEY` = your key
6. Deploy — you'll get a URL like `your-app.onrender.com`

### Option B: Railway

1. Push to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variable: `ANTHROPIC_API_KEY` = your key
4. Railway auto-detects the Procfile and deploys

### Custom Domain

After deploying on Render or Railway:
1. Buy a domain (Namecheap, Cloudflare, etc.) — ~$10-15/year
2. In your hosting dashboard, go to Settings → Custom Domain
3. Add your domain and update DNS records as instructed

---

## Cost Estimate

- **Hosting:** Free (Render/Railway free tiers)
- **Domain:** ~$10-15/year
- **Claude API:** ~$0.003 per chat message (Sonnet)
  - 50 chats/day ≈ **$5-10/month**
  - 10 chats/day ≈ **$1-2/month**

---

## Customization

### Updating Business Info
Edit the `SYSTEM_PROMPT` in `server.py` to change services, pricing, phone number, or any business details the chatbot knows.

### Adding Formspree (Email Contact Form)
To make the contact form actually send emails:
1. Sign up at [formspree.io](https://formspree.io) (free, 50 submissions/month)
2. Create a form and get your endpoint URL
3. In `static/index.html`, change the form tag to:
   ```html
   <form class="contact-form" action="https://formspree.io/f/YOUR_ID" method="POST">
   ```
4. Remove the `onsubmit="handleSubmit(event)"` attribute

### Rate Limiting
The server caps conversations at 20 messages and responses at 300 tokens to keep costs low. Adjust `MAX_TURNS` and `max_tokens` in `server.py` if needed.
