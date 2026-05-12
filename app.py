import os
import json
import streamlit as st
from groq import Groq

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Halo — AI WhatsApp Sales Assistant",
    page_icon="🌐",
    layout="wide",
)

# ── Premium dark CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ─── Global reset & base ─── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #0a0a0f !important;
    color: #e2e8f0 !important;
}
[data-testid="stMain"] {
    background-color: #0a0a0f !important;
}

/* ─── Hide default Streamlit chrome ─── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

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

/* ─── Error/info boxes ─── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border: 1px solid rgba(239, 68, 68, 0.3) !important;
    background: rgba(239, 68, 68, 0.08) !important;
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
.glass-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    backdrop-filter: blur(12px);
}
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
    font-size: 1.4rem;
    font-weight: 800;
    color: #f1f5f9;
    margin: 0 0 4px 0;
}
.chat-header-left p {
    font-size: 0.85rem;
    color: #94a3b8;
    margin: 0;
}
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
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}
.sidebar-logo {
    font-size: 1.3rem;
    font-weight: 900;
    color: #a78bfa;
    letter-spacing: -0.02em;
    margin-bottom: 4px;
}
.sidebar-tagline {
    font-size: 0.72rem;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 20px;
}
.sidebar-brand-card {
    background: rgba(139,92,246,0.08);
    border: 1px solid rgba(139,92,246,0.18);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 8px;
}
.sidebar-brand-card p {
    margin: 0;
    font-size: 0.82rem;
    color: #94a3b8;
}
.sidebar-brand-card strong {
    color: #e2e8f0;
    font-weight: 700;
}
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

# ── Initialize Groq ───────────────────────────────────────────────────────────
api_key = os.environ.get("GROQ_API_KEY") or (
    st.secrets.get("GROQ_API_KEY") if hasattr(st, "secrets") else None
)
if not api_key:
    st.error("⚠️ Groq API key not found. Please add GROQ_API_KEY as a secret.")
    st.stop()
client = Groq(api_key=api_key)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "brand_config" not in st.session_state:
    st.session_state.brand_config = None
if "setup_done" not in st.session_state:
    st.session_state.setup_done = False


# ── Core logic (unchanged) ────────────────────────────────────────────────────
def get_system_prompt(brand):
    return f"""Tu {brand["name"]} ka AI sales assistant hai. Tu ek experienced, friendly aur smart sales person ki tarah behave karta hai.

BRAND INFO:
- Brand Name: {brand["name"]}
- Industry/Category: {brand["industry"]}
- Brand Tone: {brand["tone"]}
- Brand Description: {brand["description"]}

PRODUCTS:
{brand["products"]}

COMMON FAQs:
{brand["faqs"]}

SPECIAL INSTRUCTIONS:
{brand["instructions"]}

TUMHARE RULES:

1. LANGUAGE: Hinglish mein baat karo — natural, friendly, jaise ek dost baat karta hai. Robotic mat bano.

2. DOMAIN EXPERT: Tu sirf brand products nahi jaanta — {brand["industry"]} ke baare mein genuinely knowledgeable hai. Agar customer koi related question pooche — skin problem, outfit advice, nutrition, etc. — genuinely help karo. Phir naturally brand product suggest karo.

3. SALES PSYCHOLOGY:
   - Customer interested lage toh gently close karo
   - Hesitant lage toh objection handle karo
   - Always value pehle, price baad mein
   - Upsell naturally karo — "is ke saath ye bhi accha rahega"

4. CONVERSATION MEMORY: Poori conversation ka context yaad rakho. Agar customer ne pehle kuch bataya hai — use use karo.

5. NEVER:
   - Robotic ya scripted mat lago
   - "Main sirf ek AI hoon" mat bolo
   - Brand ke baare mein galat info mat do
   - Aggressive sales mat karo

6. ALWAYS:
   - Warm aur helpful raho
   - Honest raho — agar product available nahi hai toh clearly bolo
   - Customer ki problem pehle samjho, phir solution do

Yaad rakho — tera goal hai customer ki genuinely help karna. Sale naturally aayegi."""


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


# ══════════════════════════════════════════════════════════════════════════════
# SETUP PAGE
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.setup_done:

    # Hero section
    st.markdown("""
    <div class="halo-hero">
        <div class="halo-badge">✦ Powered by Halo</div>
        <h1>Launch your AI WhatsApp<br>Sales Assistant</h1>
        <p>Train Halo with your brand details, products, FAQs, and policies — go live in minutes.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("brand_setup"):
        col1, col2 = st.columns(2, gap="large")

        with col1:
            # Brand Identity
            st.markdown('<div class="section-label">Brand Identity</div>', unsafe_allow_html=True)
            with st.container():
                brand_name = st.text_input(
                    "Brand Name *",
                    placeholder="e.g. The Outfit Room",
                )
                industry = st.selectbox(
                    "Industry *",
                    [
                        "Clothing & Fashion",
                        "Skincare & Beauty",
                        "Food & Nutrition",
                        "Electronics",
                        "Home & Decor",
                        "Fitness & Health",
                        "Jewellery",
                        "Other",
                    ],
                )
                tone = st.selectbox(
                    "Brand Tone *",
                    [
                        "Friendly & Casual (Hinglish)",
                        "Professional & Formal",
                        "Youthful & Trendy",
                        "Luxury & Premium",
                        "Warm & Personal",
                    ],
                )

            # Brand description
            st.markdown('<div class="section-label">Brand Story</div>', unsafe_allow_html=True)
            description = st.text_area(
                "Brand Description *",
                placeholder="Tell Halo about your brand — what you sell, what makes you special, and who your customers are.",
                height=130,
            )

        with col2:
            # Products
            st.markdown('<div class="section-label">Products & Offers</div>', unsafe_allow_html=True)
            products = st.text_area(
                "Products List *",
                placeholder="1. Flying Machine Slim Fit Jeans — ₹1299 — Sizes: 28–36\n2. Premium Oxford Shirt — ₹899 — Colors: White, Blue, Black\n3. Casual Hoodie — ₹799 — Sizes: S, M, L, XL",
                height=140,
            )

            # FAQs
            st.markdown('<div class="section-label">FAQs & Policies</div>', unsafe_allow_html=True)
            faqs = st.text_area(
                "Common Questions & Answers",
                placeholder="Q: Delivery kitne din mein hogi?\nA: 3–5 business days\n\nQ: Return policy kya hai?\nA: 7 din return policy hai",
                height=110,
            )

            # AI Instructions
            st.markdown('<div class="section-label">AI Instructions</div>', unsafe_allow_html=True)
            instructions = st.text_area(
                "Special Instructions (Optional)",
                placeholder="Active offers, discount codes, seasonal promotions, or any rules for the assistant to follow.",
                height=80,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "🚀  Launch Halo Assistant", use_container_width=True
        )

        if submitted:
            if not brand_name or not description or not products:
                st.error("Brand name, description, and products are required to launch.")
            else:
                brand_cfg = {
                    "name": brand_name,
                    "industry": industry,
                    "tone": tone,
                    "description": description,
                    "products": products,
                    "faqs": faqs if faqs else "No specific FAQs provided",
                    "instructions": instructions if instructions else "None",
                }
                st.session_state.brand_config = brand_cfg
                st.session_state.setup_done = True

                # Save active brand for webhook.py
                with open("active_brand.json", "w") as f:
                    json.dump(brand_cfg, f)

                # Welcome message
                welcome = f"Hey! 👋 Main {brand_name} ka assistant hoon. Kaise help kar sakta hoon aapki?"
                st.session_state.messages.append({"role": "assistant", "content": welcome})
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# CHAT PAGE
# ══════════════════════════════════════════════════════════════════════════════
else:
    brand = st.session_state.brand_config

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown('<div class="sidebar-logo">◈ Halo</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-tagline">AI WhatsApp Sales Assistant</div>', unsafe_allow_html=True)

        st.markdown("---")

        st.markdown('<div class="section-label">Active Brand</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="sidebar-brand-card">
            <p><strong>{brand["name"]}</strong></p>
            <p>{brand["industry"]}</p>
            <p style="color:#6d28d9;font-size:0.75rem;margin-top:4px;">{brand["tone"]}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown('<div class="section-label">Session Stats</div>', unsafe_allow_html=True)
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

        if st.button("⚙️  New Brand Setup", use_container_width=True):
            st.session_state.setup_done = False
            st.session_state.messages = []
            st.session_state.brand_config = None
            st.rerun()

        st.markdown("---")

        st.markdown('<div class="section-label">Quick Test Prompts</div>', unsafe_allow_html=True)
        test_prompts = [
            "Products dikhao",
            "Price kya hai?",
            "Delivery kitne din?",
            "Return policy?",
            "Kaunsa best hai?",
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
            <p>{brand["industry"]} &nbsp;·&nbsp; {brand["tone"]}</p>
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
