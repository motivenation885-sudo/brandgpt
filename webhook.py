"""
Halo — WhatsApp Webhook (Flask)
Runs on port 5001. Give Twilio the port-5001 Replit URL.
POST /webhook  → Twilio → Groq → TwiML reply
GET  /webhook  → health check JSON
GET  /webhook-test → plain text
"""

from __future__ import annotations

import logging
import os
import time
import json
from xml.sax.saxutils import escape
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, Response
from groq import Groq, APITimeoutError

app = Flask(__name__)
log = logging.getLogger("halo.webhook")
_executor = ThreadPoolExecutor(max_workers=4)

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_TIMEOUT = 12
MAX_TOKENS = 400
TEMPERATURE = 0.7
MAX_HISTORY = 8

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
HANDOFF_COOLDOWN = 30 * 60

_conversations: dict[str, list[dict]] = {}
_paused: dict[str, float] = {}
_client: Groq | None = None


def _groq() -> Groq:
    global _client
    if _client is None:
        key = os.environ.get("GROQ_API_KEY", "")
        if not key:
            raise RuntimeError("GROQ_API_KEY not set")
        _client = Groq(api_key=key)
    return _client


_BRAND_FILE = "active_brand.json"


def _load_brand() -> dict | None:
    try:
        if os.path.exists(_BRAND_FILE):
            with open(_BRAND_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def _build_prompt(brand: dict) -> str:
    return f"""You are the WhatsApp sales assistant for {brand["name"]}. You are a warm, smart, consultative salesperson.

BRAND:
- Name: {brand["name"]}
- Category: {brand["industry"]}
- Tone: {brand["tone"]}
- Description: {brand["description"]}

PRODUCTS (use ONLY these, never invent):
{brand["products"]}

FAQs:
{brand.get("faqs", "None")}

SPECIAL INSTRUCTIONS:
{brand.get("instructions", "None")}

RULES:
1. LANGUAGE: Natural Hinglish — Hindi in English script mixed with English. If customer writes only English, reply in English.
2. GREETING: Introduce yourself ONLY in the very first message. Never repeat name or welcome after that.
3. REPLY LENGTH: Simple message (hi, ok, thanks) = 1-2 lines. Product question = 3-4 lines. Never dump all products unless asked.
4. PRODUCT KNOWLEDGE: Use ONLY products listed above. Never invent prices or availability.
5. SALES: Understand need first, recommend ONE specific product. Handle price objection with value. No bullet points, no headers, plain WhatsApp chat style.
6. NEVER: Make up product info. Be pushy. Repeat greeting. Use bullet points or markdown."""


_INTENT_PROMPT = """Classify this customer message. Be VERY conservative.

NEEDS_HUMAN only if:
- Explicitly asks for human, manager, agent
- Specific order problem (wrong/damaged item received)
- Very abusive language
- Refund for specific past order

BOT_CAN_HANDLE for everything else including price concerns, product questions, return policy, delivery, comparisons, discount requests.

Reply ONE word only: NEEDS_HUMAN or BOT_CAN_HANDLE"""


def _needs_human(message: str) -> bool:
    try:
        resp = _groq().chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": _INTENT_PROMPT},
                {"role": "user", "content": message},
            ],
            max_tokens=5,
            temperature=0,
            timeout=GROQ_TIMEOUT,
        )
        return "NEEDS_HUMAN" in resp.choices[0].message.content.strip().upper()
    except Exception:
        return False


def _send_telegram_alert(sender: str, message: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        import requests as req
        text = f"HANDOFF ALERT\nCustomer: {sender}\nMessage: {message}\nTime: {time.strftime('%H:%M:%S')}"
        req.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=5,
        )
    except Exception:
        pass


def _generate_reply(brand: dict, sender: str, message: str) -> str:
    history = _conversations.get(sender, [])
    messages = [{"role": "system", "content": _build_prompt(brand)}]
    messages.extend(history[-MAX_HISTORY:])
    messages.append({"role": "user", "content": message})

    resp = _groq().chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        timeout=GROQ_TIMEOUT,
    )
    reply = resp.choices[0].message.content.strip()

    if sender not in _conversations:
        _conversations[sender] = []
    _conversations[sender].append({"role": "user", "content": message})
    _conversations[sender].append({"role": "assistant", "content": reply})
    if len(_conversations[sender]) > MAX_HISTORY:
        _conversations[sender] = _conversations[sender][-MAX_HISTORY:]

    return reply


def _twiml(text: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escape(text)}</Message></Response>'


def _send_twiml(text: str):
    """Build TwiML, log it, and return a Flask Response with correct headers."""
    twiml = _twiml(text)
    print(f"[HALO TWIML RESPONSE]\n{twiml}\n", flush=True)
    resp = Response(twiml, status=200, mimetype="text/xml")
    resp.headers["Content-Type"] = "text/xml; charset=utf-8"
    return resp


@app.route("/webhook", methods=["GET"])
def webhook_get():
    return {"status": "Halo webhook live"}, 200


@app.route("/webhook-test", methods=["GET"])
def webhook_test():
    return Response("Webhook is alive", mimetype="text/plain")


@app.route("/webhook", methods=["POST"])
def webhook_post():
    # ── 1. Log the full incoming request ─────────────────────────────────────
    print("[HALO INCOMING REQUEST]", flush=True)
    print(f"  Method : {request.method}", flush=True)
    print(f"  URL    : {request.url}", flush=True)
    print(f"  Headers: {dict(request.headers)}", flush=True)
    print(f"  Form   : {dict(request.form)}", flush=True)

    sender  = (request.form.get("From", "") or "").strip()
    message = (request.form.get("Body", "") or "").strip()

    print(f"  From   : {sender}", flush=True)
    print(f"  Body   : {message}", flush=True)

    if not sender or not message:
        return _send_twiml("Message nahi mila. Dobara try karo.")

    brand = _load_brand()
    if brand is None:
        return _send_twiml("Brand setup nahi hai. Pehle Halo app mein brand configure karo.")

    if _paused.get(sender, 0) > time.time():
        twiml = '<?xml version="1.0" encoding="UTF-8"?><Response/>'
        print(f"[HALO TWIML RESPONSE]\n{twiml}\n", flush=True)
        resp = Response(twiml, status=200, mimetype="text/xml")
        resp.headers["Content-Type"] = "text/xml; charset=utf-8"
        return resp

    if message.lower().strip() in {"reset", "clear", "/reset"}:
        _conversations.pop(sender, None)
        return _send_twiml(
            f"Conversation reset! Main {brand['name']} ka assistant hoon, kaise help karoon?"
        )

    if _needs_human(message):
        _send_telegram_alert(sender, message)
        _paused[sender] = time.time() + HANDOFF_COOLDOWN
        _conversations.pop(sender, None)
        return _send_twiml(
            "I understand this needs personal attention. "
            "Let me connect you with our team — they'll reach out shortly! 🙏"
        )

    try:
        reply = _generate_reply(brand, sender, message)
    except APITimeoutError:
        reply = "Thodi der mein dobara try karo!"
    except Exception:
        log.exception("Reply generation failed")
        reply = "Kuch issue aa gaya. Thodi der mein dobara try karo."

    return _send_twiml(reply)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
