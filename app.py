import os
import io
import re
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

# ── Premium light CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ─── Global reset & base ─── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"],
[data-testid="stMain"], .main, .block-container {
    background: #EEF3F8 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #101828 !important;
}
[data-testid="stMain"] {
    background: radial-gradient(ellipse 90% 50% at 70% -5%, rgba(6,182,212,0.06) 0%, transparent 55%),
                radial-gradient(ellipse 60% 40% at 0% 90%, rgba(29,78,216,0.04) 0%, transparent 60%),
                #EEF3F8 !important;
}

/* ─── Hide default Streamlit chrome ─── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* ─── Sidebar collapse controls — always visible ─── */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"] {
    visibility: visible !important;
    display: flex !important;
    z-index: 999 !important;
}
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarCollapsedControl"] button {
    background: #ffffff !important;
    border: 1px solid #E5E7EB !important;
    color: #4F46E5 !important;
    border-radius: 8px !important;
    visibility: visible !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important;
}
[data-testid="baseButton-headerNoPadding"] {
    visibility: visible !important;
    color: #4F46E5 !important;
}

/* ─── Sidebar ─── */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #E5E7EB !important;
    box-shadow: 2px 0 16px rgba(0,0,0,0.04) !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown span,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div { color: #374151 !important; }
[data-testid="stSidebar"] hr { border-color: #F3F4F6 !important; }

/* ─── Block container padding ─── */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 5rem !important;
    max-width: 900px !important;
}

/* ─── Inputs & selects ─── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] > div > div {
    background: #ffffff !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 10px !important;
    color: #111827 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #06B6D4 !important;
    box-shadow: 0 0 0 3px rgba(6,182,212,0.12) !important;
    outline: none !important;
}
label, [data-testid="stWidgetLabel"] p {
    color: #6B7280 !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}

/* ─── Buttons ─── */
[data-testid="stButton"] > button {
    background: #ffffff !important;
    border: 1px solid #E5E7EB !important;
    color: #374151 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    transition: all 0.18s ease !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}
[data-testid="stButton"] > button:hover {
    background: #E0F7FA !important;
    border-color: #06B6D4 !important;
    color: #0E7490 !important;
    box-shadow: 0 2px 8px rgba(6,182,212,0.15) !important;
}

/* ─── Sidebar buttons ─── */
[data-testid="stSidebar"] [data-testid="stButton"] > button {
    background: #F9FAFB !important;
    border: 1px solid #E5E7EB !important;
    color: #374151 !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] > button:hover {
    background: #E0F7FA !important;
    border-color: #06B6D4 !important;
    color: #0E7490 !important;
}

/* ─── Form submit button ─── */
[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #06B6D4 0%, #0891B2 100%) !important;
    border: none !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    padding: 0.75rem 2rem !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 4px 20px rgba(6,182,212,0.35) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    box-shadow: 0 6px 28px rgba(6,182,212,0.5) !important;
    transform: translateY(-1px) !important;
}

/* ─── File uploader ─── */
[data-testid="stFileUploader"] section {
    background: #ffffff !important;
    border: 1.5px dashed #A5F3FC !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploader"] section:hover {
    border-color: #06B6D4 !important;
    background: #E0F7FA !important;
}
[data-testid="stFileUploader"] button {
    background: #E0F7FA !important;
    border: 1px solid #A5F3FC !important;
    color: #0E7490 !important;
    border-radius: 8px !important;
}

/* ─── Dataframe ─── */
[data-testid="stDataFrame"] {
    border: 1px solid #E5E7EB !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    background: #ffffff !important;
}

/* ─── Checkbox ─── */
[data-testid="stCheckbox"] label p {
    text-transform: none !important;
    letter-spacing: normal !important;
    font-size: 0.9rem !important;
    color: #374151 !important;
}

/* ─── Divider ─── */
hr { border-color: #F3F4F6 !important; }

/* ─── Expander ─── */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 12px !important;
}

/* ─── Chat messages ─── */
[data-testid="stChatMessage"] {
    background: #ffffff !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 16px !important;
    margin-bottom: 10px !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.05) !important;
}
[data-testid="stChatMessage"][data-testid*="user"],
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: #EEF2FF !important;
    border-color: #C7D2FE !important;
}

/* ─── Chat input — fix the white strip bug ─── */
[data-testid="stBottom"] {
    background: transparent !important;
    border-top: none !important;
    box-shadow: none !important;
    padding-bottom: 0 !important;
}
[data-testid="stBottom"] > div {
    background: transparent !important;
}
[data-testid="stChatInput"] {
    background: #ffffff !important;
    border: 1.5px solid #E5E7EB !important;
    border-radius: 24px !important;
    box-shadow: 0 2px 16px rgba(0,0,0,0.08) !important;
    overflow: hidden !important;
}
[data-testid="stChatInput"] > div {
    background: #ffffff !important;
    border-radius: 24px !important;
}
[data-testid="stChatInput"] textarea {
    background: #ffffff !important;
    border: none !important;
    border-radius: 24px !important;
    color: #111827 !important;
    font-size: 0.95rem !important;
    padding: 14px 18px !important;
    box-shadow: none !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #9CA3AF !important; }
[data-testid="stChatInput"] textarea:focus {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #06B6D4, #0891B2) !important;
    border-radius: 50% !important;
    border: none !important;
    margin: 6px !important;
    box-shadow: 0 2px 8px rgba(6,182,212,0.4) !important;
}
[data-testid="stChatInput"] button:hover {
    box-shadow: 0 4px 14px rgba(6,182,212,0.55) !important;
}
[data-testid="stChatInput"] button svg { fill: #ffffff !important; }

/* ─── Spinner ─── */
[data-testid="stSpinner"] { color: #06B6D4 !important; }

/* ─── Alert/info boxes ─── */
[data-testid="stAlert"] { border-radius: 12px !important; }

/* ─── Selectbox dropdown ─── */
[data-testid="stSelectbox"] [role="listbox"] {
    background: #ffffff !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 10px !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.1) !important;
}

/* ─── Custom component classes ─── */

/* ── Shared utilities ── */
.section-kicker {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #06B6D4;
    margin: 0 0 8px 0;
}
.section-title {
    font-size: 1.45rem;
    font-weight: 800;
    color: #101828;
    margin: 0 0 6px 0;
    letter-spacing: -0.02em;
    line-height: 1.25;
}
.section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #06B6D4;
    margin-bottom: 4px;
    margin-top: 20px;
}
.helper-text {
    font-size: 0.78rem;
    color: #667085;
    margin: 6px 0 10px 0;
    line-height: 1.5;
}

/* ── Top brand bar ── */
.halo-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 28px;
}
.halo-logo-wrap {
    display: flex;
    align-items: center;
    gap: 12px;
}
.halo-logo-mark {
    width: 40px; height: 40px;
    border-radius: 50%;
    background: conic-gradient(#06B6D4 0deg 210deg, #0B1220 210deg 360deg);
    box-shadow: 0 0 0 3px rgba(6,182,212,0.2), 0 4px 16px rgba(6,182,212,0.2);
    flex-shrink: 0;
}
.halo-logo-text { line-height: 1.15; }
.halo-logo-name {
    font-size: 1.15rem;
    font-weight: 900;
    color: #101828;
    letter-spacing: -0.03em;
}
.halo-logo-sub {
    font-size: 0.68rem;
    font-weight: 500;
    color: #64748B;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.halo-topbar-badges {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}
.halo-topbar-badge {
    background: #E0F7FA;
    border: 1px solid #D8E3ED;
    color: #0E7490;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 5px 12px;
    border-radius: 999px;
}

/* ── Hero shell ── */
.hero-shell {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 28px;
    align-items: start;
    margin-bottom: 36px;
}
@media (max-width: 700px) { .hero-shell { grid-template-columns: 1fr; } }
.hero-copy {
    padding: 8px 0;
}
.hero-eyebrow {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #06B6D4;
    background: #E0F7FA;
    border: 1px solid #D8E3ED;
    padding: 4px 12px;
    border-radius: 999px;
    margin-bottom: 18px;
}
.hero-copy h1 {
    font-size: 2.2rem;
    font-weight: 900;
    color: #101828;
    margin: 0 0 14px 0;
    line-height: 1.12;
    letter-spacing: -0.03em;
}
.hero-copy p {
    font-size: 0.97rem;
    color: #667085;
    margin: 0 0 24px 0;
    line-height: 1.65;
}
.hero-cta-row {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 16px;
}
.halo-primary-button {
    display: inline-block;
    background: #06B6D4;
    color: #ffffff;
    font-size: 0.9rem;
    font-weight: 700;
    padding: 11px 22px;
    border-radius: 10px;
    border: none;
    cursor: pointer;
    box-shadow: 0 4px 16px rgba(6,182,212,0.35);
    transition: box-shadow 0.18s, transform 0.18s;
    letter-spacing: 0.01em;
    text-decoration: none;
}
.halo-primary-button:hover {
    box-shadow: 0 6px 22px rgba(6,182,212,0.5);
    transform: translateY(-1px);
}
.halo-secondary-button {
    display: inline-block;
    background: #ffffff;
    color: #101828;
    font-size: 0.9rem;
    font-weight: 600;
    padding: 10px 20px;
    border-radius: 10px;
    border: 1.5px solid #D8E3ED;
    cursor: pointer;
    transition: border-color 0.18s, background 0.18s;
    text-decoration: none;
}
.halo-secondary-button:hover {
    border-color: #06B6D4;
    background: #E0F7FA;
}
.hero-trust {
    font-size: 0.76rem;
    color: #667085;
    line-height: 1.5;
}
.hero-trust strong { color: #101828; }

/* ── Hero demo card ── */
.hero-demo-card {
    background: #0B1220;
    border-radius: 20px;
    padding: 22px 22px 18px 22px;
    box-shadow: 0 8px 40px rgba(11,18,32,0.28);
    position: relative;
    overflow: hidden;
}
.hero-demo-card::before {
    content: "";
    position: absolute;
    top: -40px; right: -40px;
    width: 180px; height: 180px;
    background: radial-gradient(circle, rgba(6,182,212,0.15) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}
.demo-toprow {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 18px;
}
.demo-title-txt {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.45);
}
.demo-status-badge {
    font-size: 0.67rem;
    font-weight: 700;
    background: rgba(6,182,212,0.18);
    border: 1px solid rgba(6,182,212,0.35);
    color: #06B6D4;
    padding: 3px 10px;
    border-radius: 999px;
    letter-spacing: 0.05em;
}
.demo-msg-label {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 4px;
}
.demo-msg-label-customer { color: rgba(255,255,255,0.35); }
.demo-msg-label-halo { color: #06B6D4; }
.demo-bubble-wrap { margin-bottom: 14px; }
.demo-msg-customer {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px 12px 12px 4px;
    padding: 10px 14px;
    font-size: 0.87rem;
    color: rgba(255,255,255,0.85);
    line-height: 1.5;
    display: inline-block;
    max-width: 90%;
}
.demo-msg-halo {
    background: rgba(6,182,212,0.12);
    border: 1px solid rgba(6,182,212,0.22);
    border-radius: 12px 12px 4px 12px;
    padding: 10px 14px;
    font-size: 0.87rem;
    color: rgba(255,255,255,0.9);
    line-height: 1.55;
    display: inline-block;
    max-width: 95%;
}
.demo-product-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 14px;
    padding-top: 14px;
    border-top: 1px solid rgba(255,255,255,0.07);
}
.demo-product-chip {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 0.7rem;
    color: rgba(255,255,255,0.5);
    font-weight: 500;
}

/* ── Feature grid ── */
.feature-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin: 0 0 36px 0;
}
@media (max-width: 600px) { .feature-grid { grid-template-columns: 1fr; } }
.feature-card {
    background: #ffffff;
    border: 1px solid #D8E3ED;
    border-radius: 16px;
    padding: 22px 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.04);
    transition: box-shadow 0.18s, transform 0.18s;
}
.feature-card:hover {
    box-shadow: 0 6px 22px rgba(6,182,212,0.12);
    transform: translateY(-2px);
}
.feature-icon {
    width: 34px; height: 34px;
    border-radius: 9px;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.fi-catalogue {
    background: #E0F7FA;
    border: 1px solid #A5F3FC;
}
.fi-campaign { background: #EFF6FF; border: 1px solid #BFDBFE; }
.fi-guided   { background: #FFF7ED; border: 1px solid #FED7AA; }
.fi-upsell   { background: #E0F7FA; border: 1px solid #A5F3FC; }
.fi-inner {
    width: 14px; height: 14px;
    border-radius: 3px;
}
.fi-inner-catalogue { background: #06B6D4; }
.fi-inner-campaign  { background: #1D4ED8; }
.fi-inner-guided    { background: #F97316; }
.fi-inner-upsell    { background: #0891B2; }
.feature-card h3 {
    font-size: 0.93rem;
    font-weight: 700;
    color: #101828;
    margin: 0 0 8px 0;
    line-height: 1.3;
}
.feature-card p {
    font-size: 0.82rem;
    color: #667085;
    margin: 0;
    line-height: 1.6;
}

/* ── Workflow grid ── */
.workflow-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin: 0 0 36px 0;
    position: relative;
}
@media (max-width: 680px) { .workflow-grid { grid-template-columns: 1fr 1fr; } }
.workflow-step-card {
    background: #ffffff;
    border: 1px solid #D8E3ED;
    border-radius: 16px;
    padding: 20px 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    position: relative;
}
.workflow-step-num {
    width: 30px; height: 30px;
    border-radius: 50%;
    background: #0B1220;
    border: 2px solid #06B6D4;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: 800;
    color: #06B6D4;
    margin-bottom: 12px;
    letter-spacing: 0.02em;
}
.workflow-step-title {
    font-size: 0.88rem;
    font-weight: 700;
    color: #101828;
    margin: 0 0 4px 0;
}
.workflow-step-desc {
    font-size: 0.77rem;
    color: #667085;
    margin: 0;
    line-height: 1.5;
}

/* ── Audience pills ── */
.audience-section {
    background: #0B1220;
    border-radius: 18px;
    padding: 28px 28px 24px 28px;
    margin: 0 0 32px 0;
}
.audience-section .section-kicker { color: rgba(6,182,212,0.9); }
.audience-section .section-title { color: #ffffff; margin-bottom: 18px; }
.audience-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}
.audience-pill {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    color: rgba(255,255,255,0.75);
    font-size: 0.82rem;
    font-weight: 500;
    padding: 7px 18px;
    border-radius: 999px;
    transition: background 0.15s, border-color 0.15s;
}
.audience-pill:hover {
    background: rgba(6,182,212,0.14);
    border-color: rgba(6,182,212,0.35);
    color: #fff;
}

/* ── Profiles section ── */
.profiles-card {
    background: #ffffff;
    border: 1px solid #D8E3ED;
    border-radius: 16px;
    padding: 22px 24px;
    margin: 0 0 8px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.profiles-card-title {
    font-size: 1rem;
    font-weight: 700;
    color: #101828;
    margin: 0 0 4px 0;
}
.profiles-card-sub {
    font-size: 0.82rem;
    color: #667085;
    margin: 0 0 18px 0;
}

/* ── Setup transition heading ── */
.setup-heading { margin: 36px 0 4px 0; }
.setup-heading h2 {
    font-size: 1.5rem;
    font-weight: 800;
    color: #101828;
    margin: 0 0 6px 0;
    letter-spacing: -0.02em;
}
.setup-heading p { font-size: 0.9rem; color: #667085; margin: 0 0 20px 0; }

/* ── Shared: profile/catalogue/upload ── */
.profile-section {
    background: #ffffff;
    border: 1px solid #D8E3ED;
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 24px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.05);
}
.profile-section-title {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #06B6D4;
    margin: 0 0 14px 0;
}
.catalogue-loaded-notice {
    background: #E0F7FA;
    border: 1px solid #D8E3ED;
    border-radius: 10px;
    padding: 10px 16px;
    margin: 10px 0 4px 0;
    font-size: 0.84rem;
    color: #0E7490;
}
.upload-summary {
    background: #EEF3F8;
    border: 1px solid #D8E3ED;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 12px 0;
}
.upload-summary p { margin: 2px 0; font-size: 0.85rem; color: #374151; }
.upload-summary strong { color: #06B6D4; font-weight: 700; }

/* ── Chat page components ── */
.chat-header {
    background: #ffffff;
    border: 1px solid #D8E3ED;
    border-radius: 18px;
    padding: 20px 28px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}
.chat-header-left h2 {
    font-size: 1.35rem;
    font-weight: 800;
    color: #101828;
    margin: 0 0 4px 0;
    letter-spacing: -0.01em;
}
.chat-header-left p { font-size: 0.83rem; color: #667085; margin: 0; }
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #E0F7FA;
    border: 1px solid #D8E3ED;
    color: #0E7490;
    font-size: 0.73rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    padding: 5px 14px;
    border-radius: 999px;
}
.status-dot {
    width: 7px; height: 7px;
    background: #06B6D4;
    border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 6px rgba(6,182,212,0.65);
    animation: pulse 2s infinite;
}
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }

/* ── Sidebar ── */
.sidebar-logo { font-size: 1.35rem; font-weight: 900; color: #06B6D4; letter-spacing: -0.03em; margin-bottom: 2px; }
.sidebar-tagline { font-size: 0.68rem; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 20px; }
.sidebar-brand-card { background: #E0F7FA; border: 1px solid #D8E3ED; border-radius: 12px; padding: 14px 16px; margin-bottom: 8px; }
.sidebar-brand-card p { margin: 0; font-size: 0.82rem; color: #667085; }
.sidebar-brand-card strong { color: #101828; font-weight: 700; }
.sidebar-stat {
    display: flex; justify-content: space-between; align-items: center;
    background: #EEF3F8; border: 1px solid #D8E3ED; border-radius: 10px;
    padding: 9px 14px; margin-bottom: 6px; font-size: 0.82rem;
}
.stat-label { color: #9CA3AF; }
.stat-value { color: #06B6D4; font-weight: 700; }

/* ── Halo badge (legacy) ── */
.halo-badge {
    display: inline-block;
    background: #E0F7FA;
    border: 1px solid #D8E3ED;
    color: #0E7490;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 999px;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
PROFILES_FILE = "saved_profiles.json"
BRANDS_DIR = "brands"


def make_brand_id(name: str) -> str:
    """Lowercase, spaces → underscores, strip special chars. 'The Outfit Room' → 'the_outfit_room'."""
    s = (name or "").lower().strip()
    s = re.sub(r"[^a-z0-9_\s-]", "", s)
    s = re.sub(r"[\s-]+", "_", s)
    return s.strip("_") or "brand"


def save_brand_file(brand_cfg: dict) -> None:
    """Persist a brand to brands/{brand_id}.json for webhook routing."""
    bid = brand_cfg.get("brand_id") or make_brand_id(brand_cfg.get("name", ""))
    os.makedirs(BRANDS_DIR, exist_ok=True)
    with open(os.path.join(BRANDS_DIR, f"{bid}.json"), "w") as f:
        json.dump(brand_cfg, f, indent=2)


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
    # Backfill brand_id / whatsapp_number for legacy profiles
    profile.setdefault("brand_id", make_brand_id(profile.get("name", "")))
    profile.setdefault("whatsapp_number", "")

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
    save_brand_file(profile)


# ══════════════════════════════════════════════════════════════════════════════
# SETUP PAGE
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.setup_done:

    # ── Top brand bar ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class="halo-topbar">
        <div class="halo-logo-wrap">
            <div class="halo-logo-mark"></div>
            <div class="halo-logo-text">
                <div class="halo-logo-name">Halo</div>
                <div class="halo-logo-sub">AI WhatsApp Sales Assistant</div>
            </div>
        </div>
        <div class="halo-topbar-badges">
            <span class="halo-topbar-badge">Catalogue-aware</span>
            <span class="halo-topbar-badge">Ad-lead ready</span>
            <span class="halo-topbar-badge">WhatsApp-first</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Hero — two-column ─────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero-shell">
        <div class="hero-copy">
            <span class="hero-eyebrow">Built for D2C brands running WhatsApp sales</span>
            <h1>Turn ad clicks into guided WhatsApp sales.</h1>
            <p>Upload your catalogue, offers, FAQs, and policies. Halo answers product questions, qualifies buyers, and guides customers from ad interest to checkout.</p>
            <div class="hero-cta-row">
                <span class="halo-primary-button">Create assistant</span>
                <span class="halo-secondary-button">Load saved profile</span>
            </div>
            <div class="hero-trust">Understands <strong>product IDs, campaign codes, sizes, colors, prices, offers,</strong> and links.</div>
        </div>
        <div class="hero-demo-card">
            <div class="demo-toprow">
                <span class="demo-title-txt">AD LEAD CAPTURED</span>
                <span class="demo-status-badge">Answered from catalogue</span>
            </div>
            <div class="demo-bubble-wrap">
                <div class="demo-msg-label demo-msg-label-customer">Customer</div>
                <div class="demo-msg-customer">Hi, I&#39;m interested in SHIRT001</div>
            </div>
            <div class="demo-bubble-wrap">
                <div class="demo-msg-label demo-msg-label-halo">Halo</div>
                <div class="demo-msg-halo">Cotton Casual Shirt &#8212; &#8377;799. Available in M / L / XL and White, Sky Blue, Navy. Which size would you prefer?</div>
            </div>
            <div class="demo-product-row">
                <span class="demo-product-chip">Size</span>
                <span class="demo-product-chip">Color</span>
                <span class="demo-product-chip">Price</span>
                <span class="demo-product-chip">Product link</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Feature cards ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class="section-kicker">Why Halo</div>
    <div class="section-title" style="margin-bottom:16px;">Product intelligence, built in.</div>
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon fi-catalogue">
                <div class="fi-inner fi-inner-catalogue"></div>
            </div>
            <h3>Product answers from catalogue</h3>
            <p>Answer price, size, color, stock, delivery, exchange, and product link questions from uploaded product data.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon fi-campaign">
                <div class="fi-inner fi-inner-campaign"></div>
            </div>
            <h3>Campaign-code aware</h3>
            <p>When leads arrive via SHIRT001 or JEANS001, Halo starts with that exact product instead of a generic reply.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon fi-guided">
                <div class="fi-inner fi-inner-guided"></div>
            </div>
            <h3>Guided selling</h3>
            <p>Ask the right follow-up: size, color, budget, use-case, or checkout intent — in the customer's natural flow.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon fi-upsell">
                <div class="fi-inner fi-inner-upsell"></div>
            </div>
            <h3>Smart upsell support</h3>
            <p>Suggest matching products, combos, and offers only when they exist in brand data. No hallucinations.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Workflow grid ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class="section-kicker">How it works</div>
    <div class="section-title" style="margin-bottom:16px;">Live in four steps.</div>
    <div class="workflow-grid">
        <div class="workflow-step-card">
            <div class="workflow-step-num">01</div>
            <div class="workflow-step-title">Upload catalogue</div>
            <p class="workflow-step-desc">Drop your product CSV with IDs, prices, sizes, colors, and campaign codes.</p>
        </div>
        <div class="workflow-step-card">
            <div class="workflow-step-num">02</div>
            <div class="workflow-step-title">Train Halo</div>
            <p class="workflow-step-desc">Add brand identity, tone, FAQs, and policies. Halo learns your brand voice.</p>
        </div>
        <div class="workflow-step-card">
            <div class="workflow-step-num">03</div>
            <div class="workflow-step-title">Connect WhatsApp</div>
            <p class="workflow-step-desc">Link your Twilio WhatsApp number. Route multiple brands using prefix codes.</p>
        </div>
        <div class="workflow-step-card">
            <div class="workflow-step-num">04</div>
            <div class="workflow-step-title">Convert leads</div>
            <p class="workflow-step-desc">Halo handles incoming chats, answers queries, and guides buyers to checkout.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Audience section ──────────────────────────────────────────────────────
    st.markdown("""
    <div class="audience-section">
        <div class="section-kicker">Who it&#39;s for</div>
        <div class="section-title">Built for brands where customers ask before buying.</div>
        <div class="audience-pills">
            <span class="audience-pill">Fashion &amp; Apparel</span>
            <span class="audience-pill">Skincare &amp; Beauty</span>
            <span class="audience-pill">Accessories &amp; Jewellery</span>
            <span class="audience-pill">Home &amp; Decor</span>
            <span class="audience-pill">Food &amp; Nutrition</span>
            <span class="audience-pill">Fitness &amp; Lifestyle</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Saved Brand Profiles ──────────────────────────────────────────────────
    profiles = load_saved_profiles()

    st.markdown("""
    <div class="profiles-card">
        <div class="profiles-card-title">Saved Brand Profiles</div>
        <div class="profiles-card-sub">Load an existing brand assistant for testing or demo.</div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        if not profiles:
            st.markdown(
                '<p style="color:#9CA3AF;font-size:0.88rem;margin:0 0 24px 0;">'
                'No saved profiles yet — fill the form below and launch to create your first profile.</p>',
                unsafe_allow_html=True,
            )
        else:
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
                    st.toast(f"'{selected_profile}' launched!", icon="✅")
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

    # ── Setup form heading ────────────────────────────────────────────────────
    st.markdown("""
    <div class="setup-heading">
        <h2>Create your assistant</h2>
        <p>Fill brand details, upload your product catalogue, and launch Halo in minutes.</p>
    </div>
    """, unsafe_allow_html=True)

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

            st.markdown('<div class="section-label">WhatsApp Routing</div>', unsafe_allow_html=True)
            whatsapp_number = st.text_input(
                "WhatsApp Number (Optional)",
                value=pf.get("whatsapp_number", ""),
                placeholder="whatsapp:+14155238886",
                help="Twilio WhatsApp number for this brand. If multiple brands share one Twilio Sandbox, use prefix routing (e.g. /outfit) instead.",
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
                    "brand_id": make_brand_id(brand_name),
                    "whatsapp_number": (whatsapp_number or "").strip(),
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

                # Multi-tenant: also save to brands/{brand_id}.json for webhook routing
                save_brand_file(brand_cfg)

                # Auto-save profile
                save_profile(brand_name, brand_cfg)

                welcome = f"Hey! 👋 Main {brand_name} ka assistant hoon. Kaise help kar sakta hoon aapki?"
                st.session_state.messages.append({"role": "assistant", "content": welcome})
                st.toast(f"Profile '{brand_name}' saved — you can load it anytime.", icon="✅")
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
            brand.setdefault("brand_id", make_brand_id(brand.get("name", "")))
            brand.setdefault("whatsapp_number", "")
            save_profile(brand["name"], brand)
            save_brand_file(brand)
            with open("active_brand.json", "w") as f:
                json.dump(brand, f)
            st.toast(f"Profile '{brand['name']}' saved!", icon="✅")

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
