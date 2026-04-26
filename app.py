import streamlit as st
import google.generativeai as genai
import json

# Page config
st.set_page_config(
    page_title="BrandBot",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    .stChatMessage { border-radius: 12px; margin-bottom: 8px; }
    .brand-header { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
    }
    .setup-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Gemini
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    st.error("⚠️ Gemini API key not found. Please add it in Streamlit secrets.")
    st.stop()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "brand_config" not in st.session_state:
    st.session_state.brand_config = None

if "setup_done" not in st.session_state:
    st.session_state.setup_done = False

def get_system_prompt(brand):
    return f"""Tu {brand['name']} ka AI sales assistant hai. Tu ek experienced, friendly aur smart sales person ki tarah behave karta hai.

BRAND INFO:
- Brand Name: {brand['name']}
- Industry/Category: {brand['industry']}
- Brand Tone: {brand['tone']}
- Brand Description: {brand['description']}

PRODUCTS:
{brand['products']}

COMMON FAQs:
{brand['faqs']}

SPECIAL INSTRUCTIONS:
{brand['instructions']}

TUMHARE RULES:

1. LANGUAGE: Hinglish mein baat karo — natural, friendly, jaise ek dost baat karta hai. Robotic mat bano.

2. DOMAIN EXPERT: Tu sirf brand products nahi jaanta — {brand['industry']} ke baare mein genuinely knowledgeable hai. Agar customer koi related question pooche — skin problem, outfit advice, nutrition, etc. — genuinely help karo. Phir naturally brand product suggest karo.

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
    
    # Build conversation history for Gemini
    history = []
    for msg in chat_history[:-1]:  # Exclude latest message
        role = "user" if msg["role"] == "user" else "model"
        history.append({
            "role": role,
            "parts": [msg["content"]]
        })
    
    # Start chat with history
    chat = model.start_chat(history=history)
    
    # Send message with system context
    full_message = f"{system_prompt}\n\nCustomer message: {user_message}"
    
    if len(chat_history) > 1:
        # After first message, don't repeat system prompt
        full_message = user_message
    
    response = chat.send_message(
        full_message if len(chat_history) <= 1 else user_message,
        generation_config=genai.types.GenerationConfig(
            temperature=0.8,
            max_output_tokens=500,
        )
    )
    
    return response.text

# SETUP PAGE
if not st.session_state.setup_done:
    st.markdown("""
    <div class="brand-header">
        <h1>🤖 BrandBot Setup</h1>
        <p>Apne brand ki info dalo — AI tumhara perfect sales assistant ban jaayega</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("brand_setup"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏷️ Brand Basics")
            brand_name = st.text_input("Brand Name *", placeholder="e.g. The Outfit Room")
            industry = st.selectbox("Industry *", [
                "Clothing & Fashion",
                "Skincare & Beauty", 
                "Food & Nutrition",
                "Electronics",
                "Home & Decor",
                "Fitness & Health",
                "Jewellery",
                "Other"
            ])
            tone = st.selectbox("Brand Tone *", [
                "Friendly & Casual (Hinglish)",
                "Professional & Formal",
                "Youthful & Trendy",
                "Luxury & Premium",
                "Warm & Personal"
            ])
            description = st.text_area(
                "Brand Description *",
                placeholder="Apne brand ke baare mein batao — kya bechte ho, kya special hai, target customer kaun hai...",
                height=120
            )
        
        with col2:
            st.markdown("### 📦 Products & FAQs")
            products = st.text_area(
                "Products List *",
                placeholder="""Example:
1. Flying Machine Slim Fit Jeans - ₹1299 - Sizes: 28-36
2. Premium Oxford Shirt - ₹899 - Colors: White, Blue, Black
3. Casual Hoodie - ₹799 - Sizes: S, M, L, XL""",
                height=150
            )
            
            faqs = st.text_area(
                "Common FAQs",
                placeholder="""Example:
Q: Delivery kitne din mein hogi?
A: 3-5 business days

Q: Return policy kya hai?
A: 7 din return policy hai""",
                height=120
            )
            
            instructions = st.text_area(
                "Special Instructions (Optional)",
                placeholder="Koi specific cheez jo AI ko jaanni chahiye — offers, discounts, special policies...",
                height=80
            )
        
        submitted = st.form_submit_button("🚀 BrandBot Launch Karo!", use_container_width=True)
        
        if submitted:
            if not brand_name or not description or not products:
                st.error("Brand name, description aur products required hain!")
            else:
                st.session_state.brand_config = {
                    "name": brand_name,
                    "industry": industry,
                    "tone": tone,
                    "description": description,
                    "products": products,
                    "faqs": faqs if faqs else "No specific FAQs provided",
                    "instructions": instructions if instructions else "None"
                }
                st.session_state.setup_done = True
                
                # Add welcome message
                welcome = f"Hey! 👋 Main {brand_name} ka assistant hoon. Kaise help kar sakta hoon aapki?"
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": welcome
                })
                st.rerun()

# CHAT PAGE
else:
    brand = st.session_state.brand_config
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div class="brand-header">
            <h2>🤖 {brand['name']} — BrandBot</h2>
            <p>AI Sales Assistant | {brand['industry']} | {brand['tone']}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("⚙️ Reset & New Brand", use_container_width=True):
            st.session_state.setup_done = False
            st.session_state.messages = []
            st.session_state.brand_config = None
            st.rerun()
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input(f"{brand['name']} se kuch poochho..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Soch raha hoon..."):
                try:
                    response = chat_with_brand(
                        prompt,
                        brand,
                        st.session_state.messages
                    )
                    st.write(response)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                except Exception as e:
                    error_msg = f"Kuch error aaya: {str(e)}"
                    st.error(error_msg)
    
    # Sidebar — Brand Info
    with st.sidebar:
        st.markdown("### 📊 Brand Info")
        st.markdown(f"**Brand:** {brand['name']}")
        st.markdown(f"**Industry:** {brand['industry']}")
        st.markdown(f"**Tone:** {brand['tone']}")
        
        st.divider()
        
        st.markdown("### 💬 Conversation")
        st.markdown(f"**Messages:** {len(st.session_state.messages)}")
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            welcome = f"Hey! 👋 Main {brand['name']} ka assistant hoon. Kaise help kar sakta hoon aapki?"
            st.session_state.messages = [{"role": "assistant", "content": welcome}]
            st.rerun()
        
        st.divider()
        st.markdown("### 🧪 Test Prompts")
        test_prompts = [
            "Products dikhao",
            "Price kya hai?",
            "Delivery kitne din?",
            "Return policy?",
            "Kaunsa best hai?"
        ]
        for tp in test_prompts:
            if st.button(tp, use_container_width=True, key=tp):
                st.session_state.messages.append({"role": "user", "content": tp})
                try:
                    response = chat_with_brand(tp, brand, st.session_state.messages)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except:
                    pass
                st.rerun()
