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
_BRANDS_DIR = "brands"

# Prefix routing for Twilio Sandbox testing (one number → many brands).
# Maps "/prefix" → brand_id (file: brands/{brand_id}.json)
_PREFIX_MAP = {
    "/outfit":   "the_outfit_room",
    "/bareform": "bareform",
}


def _read_brand_file(path: str) -> dict | None:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def _load_brand(to_number: str | None = None, message_body: str | None = None):
    """
    Multi-tenant brand routing.

    Returns: (brand: dict | None, cleaned_message: str, routing_method: str)
      routing_method ∈ {"prefix", "whatsapp_number", "fallback", "none"}
    """
    msg = (message_body or "").strip()
    cleaned = msg

    # A. Prefix test routing
    if msg:
        first_token = msg.split(None, 1)[0].lower()
        if first_token in _PREFIX_MAP:
            bid = _PREFIX_MAP[first_token]
            path = os.path.join(_BRANDS_DIR, f"{bid}.json")
            brand = _read_brand_file(path)
            if brand is not None:
                # Strip the prefix (and the single space after it, if any)
                rest = msg[len(first_token):].lstrip()
                return brand, rest, "prefix"

    # B. WhatsApp "To" number routing
    to_norm = (to_number or "").strip()
    if to_norm and os.path.isdir(_BRANDS_DIR):
        try:
            for fname in os.listdir(_BRANDS_DIR):
                if not fname.endswith(".json"):
                    continue
                b = _read_brand_file(os.path.join(_BRANDS_DIR, fname))
                if not b:
                    continue
                wa = (b.get("whatsapp_number") or "").strip()
                if wa and wa == to_norm:
                    return b, cleaned, "whatsapp_number"
        except Exception:
            pass

    # C. Fallback to active_brand.json (legacy single-brand behaviour)
    if os.path.exists(_BRAND_FILE):
        b = _read_brand_file(_BRAND_FILE)
        if b is not None:
            return b, cleaned, "fallback"

    return None, cleaned, "none"


def _build_prompt(brand: dict) -> str:
    uc = bool(brand.get("use_uploaded_catalogue")) and bool(brand.get("uploaded_product_context"))
    p = [f'You are the WhatsApp sales assistant for {brand["name"]}. Warm, smart, consultative.',
         f'BRAND: {brand["name"]} | {brand["industry"]} | {brand["tone"]} — {brand["description"]}', ""]
    if uc:
        p += ["PRIMARY PRODUCT CATALOGUE:", brand["uploaded_product_context"], ""]
        if brand.get("campaign_lookup"): p += [brand["campaign_lookup"], ""]
        if brand.get("products"): p += ["EXTRA PRODUCT NOTES:", brand["products"], ""]
        p += ["CATALOGUE RULES: Source of truth. campaign_code/product_id/name → answer that product first.",
              "Never invent sizes, colors, prices, stock, offers, or links. Missing detail → say not listed."]
    else:
        p += ["PRODUCTS (use ONLY these, never invent):", brand.get("products", ""), ""]
    p += [f'FAQs: {brand.get("faqs", "None")}', f'INSTRUCTIONS: {brand.get("instructions", "None")}', "",
          "RULES: 1)Natural Hinglish; English if customer writes English. 2)Greet ONLY first message.",
          "3)1-2 lines simple / 3-4 lines product query. No markdown. 4)Only listed products, never invent.",
          "5)Need first, ONE recommendation, value before price, no pushiness."]
    return "\n".join(p)


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
    to_num  = (form.get("To",   "") or "").strip()

    print("WEBHOOK_POST_RECEIVED", flush=True)
    print(f"FROM={sender}",            flush=True)
    print(f"BODY={message}",           flush=True)
    print(f"INCOMING_TO_NUMBER={to_num}", flush=True)

    if not sender or not message:
        return _twiml_response("Message nahi mila. Dobara try karo.")

    brand, message, routing_method = _load_brand(to_number=to_num, message_body=message)
    print(f"MULTITENANT_ROUTING_METHOD={routing_method}", flush=True)

    if brand is None:
        print("LOADED_BRAND_ID=NONE", flush=True)
        print("LOADED_BRAND_NAME=NONE", flush=True)
        print("ACTIVE_BRAND_LOADED=NONE", flush=True)
        return _twiml_response(
            "Brand setup nahi hai. Pehle Halo app mein brand configure karo."
        )

    print(f"LOADED_BRAND_ID={brand.get('brand_id', '')}", flush=True)
    print(f"LOADED_BRAND_NAME={brand['name']}", flush=True)
    print(f"ACTIVE_BRAND_LOADED={brand['name']}", flush=True)

    # If prefix routing stripped the body to empty, treat as a greeting
    if not message:
        message = "hi"
    _uc = bool(brand.get("use_uploaded_catalogue")) and bool(brand.get("uploaded_product_context"))
    print(f"WEBHOOK_CATALOGUE_CONTEXT_USED={str(_uc).lower()}", flush=True)
    print(f"WEBHOOK_CAMPAIGN_LOOKUP_USED={str(_uc and bool(brand.get('campaign_lookup'))).lower()}", flush=True)

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
