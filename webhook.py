"""
Halo — WhatsApp Webhook
Mounted as Starlette routes inside Streamlit's own Uvicorn server.
Streamlit 1.57 uses Starlette/Uvicorn (NOT Tornado).
serve.py monkeypatches create_starlette_app to prepend these routes.
"""

from __future__ import annotations

import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from xml.sax.saxutils import escape

from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route

from groq import Groq, APITimeoutError

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
            with open(_BRAND_FILE) as f:
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
3. REPLY LENGTH: 1-2 lines for simple messages, 3-4 lines for product questions. Never dump all products unless asked.
4. PRODUCT KNOWLEDGE: Use ONLY products listed above. Never invent prices or availability.
5. SALES: Understand need first, recommend ONE specific product. Handle price objection with value. Plain WhatsApp chat style, no markdown.
6. NEVER: Make up product info. Be pushy. Repeat greeting. Use bullet points or headers."""


_INTENT_PROMPT = """Classify this customer message. Be VERY conservative.

NEEDS_HUMAN only if:
- Explicitly asks for human, manager, agent
- Specific order problem (wrong/damaged item received)
- Very abusive language
- Refund for specific past order

BOT_CAN_HANDLE for everything else.

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
        text = (
            f"HANDOFF ALERT\nCustomer: {sender}\n"
            f"Message: {message}\nTime: {time.strftime('%H:%M:%S')}"
        )
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

    _conversations.setdefault(sender, [])
    _conversations[sender].append({"role": "user", "content": message})
    _conversations[sender].append({"role": "assistant", "content": reply})
    if len(_conversations[sender]) > MAX_HISTORY:
        _conversations[sender] = _conversations[sender][-MAX_HISTORY:]

    return reply


def _twiml(text: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Message>{escape(text)}</Message></Response>"
    )


def _twiml_response(text: str) -> Response:
    twiml = _twiml(text)
    print(f"FINAL_TWIML_RETURNED={twiml}", flush=True)
    return Response(
        content=twiml,
        status_code=200,
        media_type="text/xml",
        headers={"Content-Type": "text/xml; charset=utf-8"},
    )


# ── Starlette route handlers ──────────────────────────────────────────────────

async def webhook_get(request: Request) -> Response:
    print("WEBHOOK_GET_OK", flush=True)
    return PlainTextResponse("Webhook alive")


async def webhook_post(request: Request) -> Response:
    form = await request.form()

    sender  = (form.get("From", "") or "").strip()
    message = (form.get("Body",  "") or "").strip()

    print("WEBHOOK_POST_RECEIVED", flush=True)
    print(f"FROM={sender}",        flush=True)
    print(f"BODY={message}",       flush=True)

    if not sender or not message:
        return _twiml_response("Message nahi mila. Dobara try karo.")

    brand = _load_brand()
    if brand is None:
        print("ACTIVE_BRAND_LOADED=NONE", flush=True)
        return _twiml_response(
            "Brand setup nahi hai. Pehle Halo app mein brand configure karo."
        )

    print(f"ACTIVE_BRAND_LOADED={brand['name']}", flush=True)

    if _paused.get(sender, 0) > time.time():
        twiml = '<?xml version="1.0" encoding="UTF-8"?><Response/>'
        print(f"FINAL_TWIML_RETURNED={twiml}", flush=True)
        return Response(
            content=twiml,
            status_code=200,
            media_type="text/xml",
            headers={"Content-Type": "text/xml; charset=utf-8"},
        )

    if message.lower().strip() in {"reset", "clear", "/reset"}:
        _conversations.pop(sender, None)
        return _twiml_response(
            f"Conversation reset! Main {brand['name']} ka assistant hoon, kaise help karoon?"
        )

    import asyncio
    loop = asyncio.get_event_loop()

    needs_human = await loop.run_in_executor(_executor, _needs_human, message)
    if needs_human:
        _send_telegram_alert(sender, message)
        _paused[sender] = time.time() + HANDOFF_COOLDOWN
        _conversations.pop(sender, None)
        return _twiml_response(
            "I understand this needs personal attention. "
            "Let me connect you with our team — they'll reach out shortly! 🙏"
        )

    try:
        reply = await loop.run_in_executor(
            _executor, _generate_reply, brand, sender, message
        )
        print(f"FINAL_REPLY={reply}", flush=True)
    except APITimeoutError:
        reply = "Thodi der mein dobara try karo!"
    except Exception:
        log.exception("Reply generation failed")
        reply = "Kuch issue aa gaya. Thodi der mein dobara try karo."

    return _twiml_response(reply)


# ── Routes list imported by serve.py ─────────────────────────────────────────
WEBHOOK_ROUTES = [
    Route("/webhook",      endpoint=webhook_get,  methods=["GET"]),
    Route("/webhook",      endpoint=webhook_post, methods=["POST"]),
    Route("/webhook-test", endpoint=webhook_get,  methods=["GET"]),
]
