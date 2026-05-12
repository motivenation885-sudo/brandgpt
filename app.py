import os
import io
import json
import streamlit as st
import pandas as pd
from groq import Groq

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Halo — AI WhatsApp Sales Assistant",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Premium dark CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ─── Global reset & base ─── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #0a0a0f !important;
    color: #e2e8f0 !important;
}
[data-testid="stMain"] { background-color: #0a0a0f !important; }

/* ─── Hide default Streamlit chrome (keep sidebar controls) ─── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* ─── Sidebar collapse/reopen controls — always visible ─── */
[data-testid="stSidebarCollapseButton"] {
    visibility: visible !important;
    display: flex !important;
}
[data-testid="stSidebarCollapseButton"] button {
    background: rgba(139, 92, 246, 0.12) !important;
    border: 1px solid rgba(139, 92, 246, 0.25) !important;
    color: #a78bfa !important;
    border-radius: 8px !important;
    visibility: visible !important;
}
[data-testid="stSidebarCollapsedControl"] {
    visibility: visible !important;
    display: flex !important;
    z-index: 999 !important;
}
[data-testid="stSidebarCollapsedControl"] button {
    background: rgba(139, 92, 246, 0.12) !important;
    border: 1px solid rgba(139, 92, 246, 0.25) !important;
    color: #a78bfa !important;
    border-radius: 0 8px 8px 0 !important;
    visibility: visible !important;
}
[data-testid="baseButton-headerNoPadding"] {
    visibility: visible !important;
    color: #a78bfa !important;
}

/* ─── Sidebar ─── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f1a 0%, #12121f 100%) !important;
    border-right: 1px solid rgba(139, 92, 246, 0.15) !important;
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }

/* ─── Inputs & selects ─── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] > div > div {
    background-color: #13131f !important;
    border: 1px solid rgba(139, 92, 246, 0.25) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: rgba(139, 92, 246, 0.6) !important;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.12) !important;
}
label, [data-testid="stWidgetLabel"] p {
    color: #94a3b8 !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}

/* ─── Buttons ─── */
[data-testid="stButton"] > button {
    background: rgba(139, 92, 246, 0.12) !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    color: #a78bfa !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
[data-testid="stButton"] > button:hover {
    background: rgba(139, 92, 246, 0.25) !important;
    border-color: rgba(139, 92, 246, 0.6) !important;
    color: #c4b5fd !important;
}

/* ─── Form submit button ─── */
[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%) !important;
    border: none !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    padding: 0.75rem 2rem !important;
    letter-spacing: 0.03em !important;
    box-shadow: 0 4px 24px rgba(124, 58, 237, 0.4) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    box-shadow: 0 6px 32px rgba(124, 58, 237, 0.6) !important;
    transform: translateY(-1px) !important;
}

/* ─── File uploader ─── */
[data-testid="stFileUploader"] section {
    background-color: #13131f !important;
    border: 1px dashed rgba(139, 92, 246, 0.4) !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploader"] section:hover {
    border-color: rgba(139, 92, 246, 0.7) !important;
    background-color: #16162a !important;
}
[data-testid="stFileUploader"] button {
    background: rgba(139, 92, 246, 0.18) !important;
    border: 1px solid rgba(139, 92, 246, 0.4) !important;
    color: #c4b5fd !important;
    border-radius: 8px !important;
}

/* ─── Dataframe ─── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(139, 92, 246, 0.18) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ─── Checkbox ─── */
[data-testid="stCheckbox"] label p {
    text-transform: none !important;
    letter-spacing: normal !important;
    font-size: 0.9rem !important;
    color: #cbd5e1 !important;
}

/* ─── Divider ─── */
hr { border-color: rgba(139, 92, 246, 0.15) !important; }

/* ─── Chat messages ─── */
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 14px !important;
    margin-bottom: 10px !important;
    backdrop-filter: blur(12px) !important;
}
[data-testid="stChatInput"] textarea {
    background-color: #13131f !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    border-radius: 14px !important;
    color: #e2e8f0 !important;
}

/* ─── Spinner ─── */
[data-testid="stSpinner"] { color: #a78bfa !important; }

/* ─── Alert/info boxes ─── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
}

/* ─── Custom component classes ─── */
.halo-hero {
    background: linear-gradient(135deg, rgba(124,58,237,0.15) 0%, rgba(109,40,217,0.08) 100%);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 20px;
    padding: 48px 40px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
}
.halo-hero::before {
    content: "";
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(139,92,246,0.18) 0%, transparent 70%);
    border-radius: 50%;
}
.halo-badge {
    display: inline-block;
    background: rgba(139, 92, 246, 0.18);
    border: 1px solid rgba(139, 92, 246, 0.35);
    color: #a78bfa;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 999px;
    margin-bottom: 20px;
}
.halo-hero h1 {
    font-size: 2.4rem;
    font-weight: 800;
    color: #f1f5f9;
    margin: 0 0 12px 0;
    line-height: 1.15;
}
.halo-hero p {
    font-size: 1.05rem;
    color: #94a3b8;
    margin: 0;
    max-width: 560px;
}
.section-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #7c3aed;
    margin-bottom: 4px;
    margin-top: 20px;
}
.helper-text {
    font-size: 0.78rem;
    color: #64748b;
    margin: 6px 0 10px 0;
    line-height: 1.5;
}
.profile-section {
    background: rgba(139, 92, 246, 0.05);
    border: 1px solid rgba(139, 92, 246, 0.18);
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 24px;
}
.profile-section-title {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #7c3aed;
    margin: 0 0 14px 0;
}
.catalogue-loaded-notice {
    background: rgba(16, 185, 129, 0.07);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 10px;
    padding: 10px 16px;
    margin: 10px 0 4px 0;
    font-size: 0.84rem;
    color: #34d399;
}
.upload-summary {
    background: rgba(16, 185, 129, 0.06);
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 12px;
    padding: 14px 18px;
    margin: 12px 0;
}
.upload-summary p { margin: 2px 0; font-size: 0.85rem; color: #cbd5e1; }
.upload-summary strong { color: #34d399; font-weight: 700; }
.chat-header {
    background: linear-gradient(135deg, rgba(124,58,237,0.12) 0%, rgba(109,40,217,0.06) 100%);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 16px;
    padding: 20px 28px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.chat-header-left h2 {
    font-size: 1.4rem; font-weight: 800; color: #f1f5f9; margin: 0 0 4px 0;
}
.chat-header-left p { font-size: 0.85rem; color: #94a3b8; margin: 0; }
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #34d399;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    padding: 5px 14px;
    border-radius: 999px;
}
.status-dot {
    width: 7px; height: 7px;
    background: #34d399;
    border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 6px #34d399;
    animation: pulse 2s infinite;
}
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
.sidebar-logo {
    font-size: 1.3rem; font-weight: 900; color: #a78bfa;
    letter-spacing: -0.02em; margin-bottom: 4px;
}
.sidebar-tagline {
    font-size: 0.72rem; color: #475569;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 20px;
}
.sidebar-brand-card {
    background: rgba(139,92,246,0.08);
    border: 1px solid rgba(139,92,246,0.18);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 8px;
}
.sidebar-brand-card p { margin: 0; font-size: 0.82rem; color: #94a3b8; }
.sidebar-brand-card strong { color: #e2e8f0; font-weight: 700; }
.sidebar-stat {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 0.83rem;
}
.stat-label { color: #64748b; }
.stat-value { color: #a78bfa; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
PROFILES_FILE = "saved_profiles.json"

INDUSTRIES = [
    "Clothing & Fashion",
    "Skincare & Beauty",
    "Food & Nutrition",
    "Electronics",
    "Home & Decor",
    "Fitness & Health",
    "Jewellery",
    "Other",
]

TONES = [
    "Friendly & Casual (Hinglish)",
    "Professional & Formal",
    "Youthful & Trendy",
    "Luxury & Premium",
    "Warm & Personal",
]

# ── Initialize Groq ───────────────────────────────────────────────────────────
api_key = os.environ.get("GROQ_API_KEY") or (
    st.secrets.get("GROQ_API_KEY") if hasattr(st, "secrets") else None
)
if not api_key:
    st.error("⚠️ Groq API key not found. Please add GROQ_API_KEY as a secret.")
    st.stop()
client = Groq(api_key=api_key)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages"         not in st.session_state: st.session_state.messages = []
if "brand_config"     not in st.session_state: st.session_state.brand_config = None
if "setup_done"       not in st.session_state: st.session_state.setup_done = False
if "parsed_catalogue" not in st.session_state: st.session_state.parsed_catalogue = None
if "prefill"          not in st.session_state: st.session_state.prefill = {}


# ══════════════════════════════════════════════════════════════════════════════
# SAVED PROFILE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def load_saved_profiles() -> dict:
    if not os.path.exists(PROFILES_FILE):
        return {}
    try:
        with open(PROFILES_FILE) as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("not a dict")
        return data
    except Exception:
        try:
            st.warning("saved_profiles.json was corrupted — resetting to empty profiles.")
        except Exception:
            pass
        save_saved_profiles({})
        return {}


def save_saved_profiles(profiles: dict) -> None:
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)


def save_profile(profile_name: str, brand_config: dict) -> None:
    profiles = load_saved_profiles()
    profiles[profile_name] = brand_config
    save_saved_profiles(profiles)


def delete_profile(profile_name: str) -> None:
    profiles = load_saved_profiles()
    profiles.pop(profile_name, None)
    save_saved_profiles(profiles)


def load_profile(profile_name: str) -> dict | None:
    profiles = load_saved_profiles()
    return profiles.get(profile_name)


# ══════════════════════════════════════════════════════════════════════════════
# CATALOGUE PARSING HELPERS
# ══════════════════════════════════════════════════════════════════════════════

REQUIRED_COLUMNS = ["product_id", "product_name", "price"]

OPTIONAL_COLUMNS = [
    "campaign_code", "category", "description", "sizes", "colors",
    "material", "fabric", "fit", "stock_status", "best_for",
    "upsell_product_ids", "offer_name", "offer_price",
    "product_link", "delivery_note", "exchange_note",
]


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [
        str(c).strip().lower().replace(" ", "_").replace("-", "_")
        for c in df.columns
    ]
    return df


def parse_product_file(uploaded_file):
    """Returns: (products: list[dict], detected_columns: list[str], error: str | None)"""
    if uploaded_file is None:
        return [], [], None

    name = (uploaded_file.name or "").lower()
    try:
        raw = uploaded_file.getvalue()
        bio = io.BytesIO(raw)
        if name.endswith(".csv"):
            df = pd.read_csv(bio)
        elif name.endswith(".xlsx") or name.endswith(".xls"):
            try:
                df = pd.read_excel(bio)
            except ImportError:
                return [], [], (
                    "Excel parsing needs 'openpyxl'. Use a CSV instead, or install openpyxl."
                )
        else:
            return [], [], "Unsupported file type. Upload a .csv or .xlsx file."
    except Exception as e:
        return [], [], f"Could not read the file: {e}"

    df = _normalize_columns(df)
    detected = list(df.columns)
    missing = [c for c in REQUIRED_COLUMNS if c not in detected]
    if missing:
        return [], detected, (
            "Product sheet must include product_id, product_name, and price. "
            f"Missing: {', '.join(missing)}."
        )

    df = df.dropna(how="all")
    products = []
    skipped = 0
    for _, row in df.iterrows():
        rec = {}
        for col in detected:
            val = row[col]
            if pd.isna(val):
                continue
            rec[col] = str(val).strip()
        if rec.get("product_id") and rec.get("product_name") and rec.get("price"):
            products.append(rec)
        else:
            skipped += 1

    if skipped and not products:
        return [], detected, (
            "All rows are missing required values (product_id, product_name, price)."
        )
    return products, detected, None


_LABELS = {
    "product_id": "Product ID", "campaign_code": "Campaign Code",
    "product_name": "Name", "category": "Category", "price": "Price",
    "description": "Description", "sizes": "Sizes", "colors": "Colors",
    "material": "Material", "fabric": "Fabric/Material", "fit": "Fit",
    "stock_status": "Stock", "best_for": "Best For",
    "upsell_product_ids": "Upsell Product IDs", "offer_name": "Offer",
    "offer_price": "Offer Price", "product_link": "Product Link",
    "delivery_note": "Delivery Note", "exchange_note": "Exchange Note",
}


def _format_price(val: str) -> str:
    s = str(val).strip()
    if not s:
        return s
    if any(ch in s for ch in "₹$€£") or any(c.isalpha() for c in s):
        return s
    try:
        n = float(s)
        return f"₹{int(n)}" if n == int(n) else f"₹{n}"
    except Exception:
        return s


def format_product_catalogue_for_prompt(products):
    if not products:
        return ""
    product_blocks = []
    field_order = [
        "product_id", "campaign_code", "product_name", "category", "price",
        "description", "sizes", "colors", "fabric", "material", "fit",
        "stock_status", "best_for", "upsell_product_ids",
        "offer_name", "offer_price", "product_link",
        "delivery_note", "exchange_note",
    ]
    for p in products:
        lines = []
        offer_name = p.get("offer_name", "").strip()
        offer_price = p.get("offer_price", "").strip()
        for key in field_order:
            if key in ("offer_name", "offer_price"):
                continue
            val = p.get(key, "")
            if not val:
                continue
            label = _LABELS.get(key, key.replace("_", " ").title())
            if key == "price":
                val = _format_price(val)
            lines.append(f"{label}: {val}")
        if offer_name or offer_price:
            offer_text = offer_name
            if offer_price:
                offer_text = f"{offer_name} at {_format_price(offer_price)}".strip(" -at")
                if not offer_name:
                    offer_text = _format_price(offer_price)
            lines.append(f"Offer: {offer_text}")
        for k, v in p.items():
            if k in field_order or k in ("offer_name", "offer_price"):
                continue
            if v:
                lines.append(f"{k.replace('_',' ').title()}: {v}")
        product_blocks.append("\n".join(lines))
    return "PRODUCT CATALOGUE TABLE:\n\n" + "\n\n---\n\n".join(product_blocks)


def build_campaign_lookup(products):
    rows = []
    for p in products:
        code = p.get("campaign_code", "").strip()
        if not code:
            continue
        rows.append(f"- {code} → {p.get('product_id','').strip()} → {p.get('product_name','').strip()}")
    if not rows:
        return ""
    return "CAMPAIGN / AD PRODUCT MAPPING:\n" + "\n".join(rows)


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ══════════════════════════════════════════════════════════════════════════════

def get_system_prompt(brand):
    use_uploaded = bool(brand.get("use_uploaded_catalogue")) and bool(
        brand.get("uploaded_product_context")
    )
    sections = [
        f'Tu {brand["name"]} ka AI sales assistant hai. Tu ek experienced, '
        f'friendly aur smart sales person ki tarah behave karta hai.',
        "",
        "BRAND INFO:",
        f'- Brand Name: {brand["name"]}',
        f'- Industry/Category: {brand["industry"]}',
        f'- Brand Tone: {brand["tone"]}',
        f'- Brand Description: {brand["description"]}',
        "",
    ]
    if use_uploaded:
        sections.append(brand["uploaded_product_context"])
        sections.append("")
        if brand.get("campaign_lookup"):
            sections.append(brand["campaign_lookup"])
            sections.append("")
        if brand.get("products"):
            sections.append("EXTRA PRODUCT NOTES (from manual list):")
            sections.append(brand["products"])
            sections.append("")
    else:
        sections.append("PRODUCTS:")
        sections.append(brand.get("products", ""))
        sections.append("")

    sections.extend([
        "COMMON FAQs:",
        brand.get("faqs", "No specific FAQs provided"),
        "",
        "SPECIAL INSTRUCTIONS:",
        brand.get("instructions", "None"),
        "",
    ])

    if use_uploaded:
        sections.append(
            "RULES FOR PRODUCT TABLE:\n"
            "- The uploaded product catalogue is the primary product source.\n"
            "- If a customer mentions a campaign_code (e.g. SHIRT001), product_id "
            "(e.g. P001), or a product name, first answer about that exact product.\n"
            "- Do not randomly show all products if the user came for one product.\n"
            "- First continue the ad/product conversation naturally.\n"
            "- Ask size/color/use-case questions if needed.\n"
            "- Only after the customer shows interest, suggest upsell_product_ids "
            "or the offer if available.\n"
            "- Use product_link when the customer wants to buy.\n"
            "- Do not invent product names, prices, sizes, colors, stock, offers, or links.\n"
            "- If something is not in the table, clearly say it is not listed in the catalogue.\n"
            "- Reply naturally in Hinglish like a WhatsApp sales advisor.\n"
            "- Keep replies short and helpful.\n"
        )

    sections.append(
        "TUMHARE GENERAL RULES:\n\n"
        "1. LANGUAGE: Hinglish mein baat karo — natural, friendly, jaise ek dost "
        "baat karta hai. Robotic mat bano.\n\n"
        f'2. DOMAIN EXPERT: Tu sirf brand products nahi jaanta — {brand["industry"]} '
        "ke baare mein genuinely knowledgeable hai. Agar customer koi related question "
        "pooche, genuinely help karo. Phir naturally brand product suggest karo.\n\n"
        "3. SALES PSYCHOLOGY:\n"
        "   - Customer interested lage toh gently close karo\n"
        "   - Hesitant lage toh objection handle karo\n"
        "   - Always value pehle, price baad mein\n"
        "   - Upsell naturally karo — \"is ke saath ye bhi accha rahega\"\n\n"
        "4. CONVERSATION MEMORY: Poori conversation ka context yaad rakho.\n\n"
        "5. NEVER:\n"
        "   - Robotic ya scripted mat lago\n"
        "   - \"Main sirf ek AI hoon\" mat bolo\n"
        "   - Brand ke baare mein galat info mat do\n"
        "   - Aggressive sales mat karo\n\n"
        "6. ALWAYS:\n"
        "   - Warm aur helpful raho\n"
        "   - Honest raho — agar product available nahi hai toh clearly bolo\n"
        "   - Customer ki problem pehle samjho, phir solution do\n\n"
        "Yaad rakho — tera goal hai customer ki genuinely help karna. "
        "Sale naturally aayegi."
    )
    return "\n".join(sections)


def chat_with_brand(user_message, brand_config, chat_history):
    system_prompt = get_system_prompt(brand_config)
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=500,
        temperature=0.8,
    )
    return response.choices[0].message.content


# ── Helper: activate a brand profile immediately ──────────────────────────────
def _activate_profile(profile: dict):
    """Set session state to go directly to chat with this profile."""
    st.session_state.brand_config = profile
    st.session_state.setup_done = True
    st.session_state.prefill = {}
    st.session_state.parsed_catalogue = None
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": f"Hey! 👋 Main {profile['name']} ka assistant hoon. Kaise help kar sakta hoon aapki?",
        }
    ]
    with open("active_brand.json", "w") as f:
        json.dump(profile, f)


# ══════════════════════════════════════════════════════════════════════════════
# SETUP PAGE
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.setup_done:

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="halo-hero">
        <div class="halo-badge">✦ Powered by Halo</div>
        <h1>Launch your AI WhatsApp<br>Sales Assistant</h1>
        <p>Train Halo with your brand details, products, FAQs, and policies — go live in minutes.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Saved Brand Profiles ──────────────────────────────────────────────────
    profiles = load_saved_profiles()
    st.markdown('<div class="profile-section-title">◈ Saved Brand Profiles</div>', unsafe_allow_html=True)

    with st.container():
        if not profiles:
            st.markdown(
                '<div class="profile-section">'
                '<p style="color:#64748b;font-size:0.88rem;margin:0;">No saved profiles yet. '
                'Fill the form below and launch to create your first saved profile.</p>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            with st.container():
                st.markdown('<div class="profile-section">', unsafe_allow_html=True)
                profile_names = list(profiles.keys())
                selected_profile = st.selectbox(
                    "Load saved profile",
                    ["— Select a saved profile —"] + profile_names,
                    key="profile_selector",
                    label_visibility="collapsed",
                )
                profile_chosen = selected_profile != "— Select a saved profile —"

                btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 1])
                with btn_col1:
                    if st.button(
                        "⚡  Quick Launch",
                        use_container_width=True,
                        disabled=not profile_chosen,
                        key="quick_launch_btn",
                        help="Activate this brand instantly without editing the form",
                    ):
                        _activate_profile(profiles[selected_profile])
                        st.toast(f"'{selected_profile}' launched!", icon="✓")
                        st.rerun()
                with btn_col2:
                    if st.button(
                        "📋  Fill Form",
                        use_container_width=True,
                        disabled=not profile_chosen,
                        key="fill_form_btn",
                        help="Pre-fill the setup form with this profile's data",
                    ):
                        prof = profiles[selected_profile]
                        st.session_state.prefill = prof
                        if prof.get("uploaded_products"):
                            st.session_state.parsed_catalogue = {
                                "products": prof["uploaded_products"],
                                "columns": prof.get("uploaded_product_columns", []),
                                "context": prof.get("uploaded_product_context", ""),
                                "campaigns": prof.get("campaign_lookup", ""),
                            }
                        else:
                            st.session_state.parsed_catalogue = None
                        st.rerun()
                with btn_col3:
                    if st.button(
                        "🗑",
                        use_container_width=True,
                        disabled=not profile_chosen,
                        key="delete_profile_btn",
                        help="Delete this saved profile",
                    ):
                        delete_profile(selected_profile)
                        if st.session_state.prefill.get("name") == selected_profile:
                            st.session_state.prefill = {}
                        st.toast(f"Profile '{selected_profile}' deleted.")
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Catalogue upload (outside form so it parses immediately) ──────────────
    pf = st.session_state.prefill  # shorthand

    # If a prefill profile already has catalogue, show notice instead of forcing re-upload
    prefill_has_catalogue = bool(pf.get("uploaded_products")) and bool(pf.get("uploaded_product_context"))

    st.markdown('<div class="section-label">Upload Product Catalogue</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="helper-text">Recommended columns: '
        '<code>product_id, campaign_code, product_name, price, sizes, colors, '
        'stock_status, upsell_product_ids, product_link</code></div>',
        unsafe_allow_html=True,
    )

    if prefill_has_catalogue and st.session_state.parsed_catalogue is not None:
        n_prods = len(pf["uploaded_products"])
        n_camp = sum(1 for p in pf["uploaded_products"] if p.get("campaign_code", "").strip())
        st.markdown(
            f'<div class="catalogue-loaded-notice">'
            f'✓ Saved catalogue loaded: <strong>{n_prods} products</strong>'
            f'{f", {n_camp} campaign codes" if n_camp else ""}'
            f' — from profile <strong>{pf.get("name","")}</strong>. '
            f'Upload a new file below to replace it.</div>',
            unsafe_allow_html=True,
        )

    uploaded = st.file_uploader(
        "Upload CSV or Excel (optional — replaces saved catalogue if present)",
        type=["csv", "xlsx"],
        help="Required columns: product_id, product_name, price",
        key="catalogue_uploader",
    )

    if uploaded is not None:
        products_parsed, detected, err = parse_product_file(uploaded)
        if err:
            st.error(err)
            if detected:
                st.caption(f"Detected columns: {', '.join(detected)}")
            # Don't wipe a valid prefill catalogue on parse error
        else:
            ctx = format_product_catalogue_for_prompt(products_parsed)
            campaigns = build_campaign_lookup(products_parsed)
            st.session_state.parsed_catalogue = {
                "products": products_parsed,
                "columns": detected,
                "context": ctx,
                "campaigns": campaigns,
            }
            campaign_count = sum(
                1 for p in products_parsed if p.get("campaign_code", "").strip()
            )
            st.markdown(
                f'<div class="upload-summary">'
                f'<p><strong>{len(products_parsed)}</strong> products detected · '
                f'<strong>{campaign_count}</strong> with campaign codes</p>'
                f'<p>Detected columns: {", ".join(detected)}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.dataframe(
                pd.DataFrame(products_parsed).head(5),
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("📄 See sample CSV template"):
        st.code(
            "product_id,campaign_code,product_name,category,price,description,"
            "sizes,colors,fabric,fit,stock_status,best_for,upsell_product_ids,"
            "offer_name,offer_price,product_link\n"
            "P001,SHIRT001,Cotton Casual Shirt,Shirt,799,"
            "Regular fit cotton shirt for office and casual wear,"
            "\"M,L,XL\",\"White,Sky Blue,Navy\",Cotton,Regular,In stock,"
            "\"office,casual,summer\",P002,Shirt + Jeans Combo,1699,"
            "https://brand.com/products/cotton-shirt\n"
            "P002,JEANS001,Slim Fit Jeans,Jeans,999,"
            "Stretch denim slim fit jeans,\"30,32,34\",\"Blue,Black\","
            "Denim,Slim Fit,In stock,\"casual,party,smart casual\",P001,"
            "Shirt + Jeans Combo,1699,"
            "https://brand.com/products/slim-fit-jeans",
            language="csv",
        )

    use_uploaded_default = st.session_state.parsed_catalogue is not None
    use_uploaded_toggle = st.checkbox(
        "Use uploaded catalogue as primary product data",
        value=use_uploaded_default,
        disabled=not use_uploaded_default,
    )

    st.markdown("---")

    # ── Brand setup form ──────────────────────────────────────────────────────
    with st.form("brand_setup"):
        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown('<div class="section-label">Brand Identity</div>', unsafe_allow_html=True)
            brand_name = st.text_input(
                "Brand Name *",
                value=pf.get("name", ""),
                placeholder="e.g. The Outfit Room",
            )
            industry_idx = INDUSTRIES.index(pf["industry"]) if pf.get("industry") in INDUSTRIES else 0
            industry = st.selectbox("Industry *", INDUSTRIES, index=industry_idx)

            tone_idx = TONES.index(pf["tone"]) if pf.get("tone") in TONES else 0
            tone = st.selectbox("Brand Tone *", TONES, index=tone_idx)

            st.markdown('<div class="section-label">Brand Story</div>', unsafe_allow_html=True)
            description = st.text_area(
                "Brand Description *",
                value=pf.get("description", ""),
                placeholder="Tell Halo about your brand — what you sell, what makes you special, and who your customers are.",
                height=130,
            )

        with col2:
            st.markdown('<div class="section-label">Products & Offers</div>', unsafe_allow_html=True)
            products_text = st.text_area(
                "Products List (manual)",
                value=pf.get("products", ""),
                placeholder="1. Flying Machine Slim Fit Jeans — ₹1299 — Sizes: 28–36\n2. Premium Oxford Shirt — ₹899 — Colors: White, Blue, Black\n3. Casual Hoodie — ₹799 — Sizes: S, M, L, XL",
                height=140,
                help="Manual product list. If a catalogue is uploaded above, this is used as extra notes.",
            )

            st.markdown('<div class="section-label">FAQs & Policies</div>', unsafe_allow_html=True)
            faqs = st.text_area(
                "Common Questions & Answers",
                value=pf.get("faqs", "") if pf.get("faqs") not in ("No specific FAQs provided", None) else "",
                placeholder="Q: Delivery kitne din mein hogi?\nA: 3–5 business days\n\nQ: Return policy kya hai?\nA: 7 din return policy hai",
                height=110,
            )

            st.markdown('<div class="section-label">AI Instructions</div>', unsafe_allow_html=True)
            pf_instructions = pf.get("instructions", "")
            instructions = st.text_area(
                "Special Instructions (Optional)",
                value=pf_instructions if pf_instructions not in ("None", None) else "",
                placeholder="Active offers, discount codes, seasonal promotions, or any rules for the assistant to follow.",
                height=80,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "🚀  Launch Halo Assistant", use_container_width=True
        )

        if submitted:
            cat = st.session_state.parsed_catalogue
            has_catalogue = cat is not None and len(cat.get("products", [])) > 0
            use_uploaded = bool(use_uploaded_toggle and has_catalogue)

            if not brand_name or not description:
                st.error("Brand name and description are required to launch.")
            elif not products_text and not has_catalogue:
                st.error("Please add a manual products list OR upload a product catalogue.")
            else:
                brand_cfg = {
                    "name": brand_name,
                    "industry": industry,
                    "tone": tone,
                    "description": description,
                    "products": products_text or "",
                    "faqs": faqs if faqs else "No specific FAQs provided",
                    "instructions": instructions if instructions else "None",
                    "uploaded_products":        cat["products"]  if has_catalogue else [],
                    "uploaded_product_columns": cat["columns"]   if has_catalogue else [],
                    "uploaded_product_context": cat["context"]   if has_catalogue else "",
                    "campaign_lookup":          cat["campaigns"] if has_catalogue else "",
                    "use_uploaded_catalogue":   use_uploaded,
                }
                st.session_state.brand_config = brand_cfg
                st.session_state.setup_done = True
                st.session_state.prefill = {}  # clear prefill after launch

                # Save active brand for webhook.py
                with open("active_brand.json", "w") as f:
                    json.dump(brand_cfg, f)

                # Auto-save profile
                save_profile(brand_name, brand_cfg)

                welcome = f"Hey! 👋 Main {brand_name} ka assistant hoon. Kaise help kar sakta hoon aapki?"
                st.session_state.messages.append({"role": "assistant", "content": welcome})
                st.toast(f"Profile '{brand_name}' saved — you can load it anytime.", icon="✓")
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# CHAT PAGE
# ══════════════════════════════════════════════════════════════════════════════
else:
    brand = st.session_state.brand_config

    uploaded_products = brand.get("uploaded_products", []) or []
    has_catalogue = len(uploaded_products) > 0
    campaign_count = sum(1 for p in uploaded_products if p.get("campaign_code", "").strip())
    use_uploaded = bool(brand.get("use_uploaded_catalogue")) and has_catalogue
    active_source = "Uploaded catalogue" if use_uploaded else "Manual products"

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown('<div class="sidebar-logo">◈ Halo</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-tagline">AI WhatsApp Sales Assistant</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Active Brand
        st.markdown('<div class="section-label">Active Brand</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="sidebar-brand-card">
            <p><strong>{brand["name"]}</strong></p>
            <p>{brand["industry"]}</p>
            <p style="color:#6d28d9;font-size:0.75rem;margin-top:4px;">{brand["tone"]}</p>
        </div>
        """, unsafe_allow_html=True)

        # Catalogue stats
        st.markdown('<div class="section-label">Product Source</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="sidebar-stat">
            <span class="stat-label">Source</span>
            <span class="stat-value">{active_source}</span>
        </div>
        <div class="sidebar-stat">
            <span class="stat-label">Products</span>
            <span class="stat-value">{len(uploaded_products) if has_catalogue else "Manual"}</span>
        </div>
        """ + (f"""
        <div class="sidebar-stat">
            <span class="stat-label">Campaign codes</span>
            <span class="stat-value">{campaign_count}</span>
        </div>
        """ if has_catalogue else "") + """
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Session
        st.markdown('<div class="section-label">Session</div>', unsafe_allow_html=True)
        msg_count = len(st.session_state.messages)
        st.markdown(f"""
        <div class="sidebar-stat">
            <span class="stat-label">Messages</span>
            <span class="stat-value">{msg_count}</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🗑️  Clear Chat", use_container_width=True):
            welcome = f"Hey! 👋 Main {brand['name']} ka assistant hoon. Kaise help kar sakta hoon aapki?"
            st.session_state.messages = [{"role": "assistant", "content": welcome}]
            st.rerun()

        st.markdown("---")

        # Profile actions
        st.markdown('<div class="section-label">Profile</div>', unsafe_allow_html=True)

        if st.button("💾  Save Current Profile", use_container_width=True):
            save_profile(brand["name"], brand)
            st.toast(f"Profile '{brand['name']}' saved!", icon="✓")

        if st.button("⚙️  New Brand Setup", use_container_width=True):
            st.session_state.setup_done = False
            st.session_state.messages = []
            st.session_state.brand_config = None
            st.session_state.parsed_catalogue = None
            st.rerun()

        st.markdown("---")

        # Quick test prompts
        st.markdown('<div class="section-label">Quick Test Prompts</div>', unsafe_allow_html=True)
        test_prompts = [
            "Products dikhao",
            "Hi I am interested in SHIRT001",
            "What sizes are available?",
            "Suggest outfit under 2000",
            "Delivery kitne din?",
        ]
        for tp in test_prompts:
            if st.button(tp, use_container_width=True, key=tp):
                st.session_state.messages.append({"role": "user", "content": tp})
                try:
                    response = chat_with_brand(tp, brand, st.session_state.messages)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception:
                    pass
                st.rerun()

    # ── Chat header ───────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="chat-header">
        <div class="chat-header-left">
            <h2>◈ {brand["name"]}</h2>
            <p>{brand["industry"]} &nbsp;·&nbsp; {brand["tone"]} &nbsp;·&nbsp; {active_source}</p>
        </div>
        <div class="status-pill">
            <span class="status-dot"></span> Live Assistant
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Chat messages ─────────────────────────────────────────────────────────
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # ── Chat input ────────────────────────────────────────────────────────────
    if prompt := st.chat_input(f"Message {brand['name']} assistant..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = chat_with_brand(prompt, brand, st.session_state.messages)
                    st.write(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Kuch error aaya: {str(e)}")
