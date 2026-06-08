"""
NTPC IT Helpdesk Chatbot + Maintenance Alert System
====================================================
Internship Project | NTPC IT Division
Built with: Python, Streamlit, Google Gemini API, Pandas

New Features Added:
  - Warranty expiry popup alerts (expired + expiring soon)
  - Vendor details shown after every AI solution
  - Vendor details in maintenance dashboard cards
  - Warranty status column in asset table
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime, date
import google.generativeai as genai

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NTPC IT Helpdesk",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0d1117;
    color: #e6edf3;
}
section[data-testid="stSidebar"] {
    background: #161b22;
    border-right: 1px solid #30363d;
}
h1, h2, h3 { font-family: 'IBM Plex Mono', monospace; }

.user-bubble {
    background: #1f6feb22;
    border: 1px solid #1f6feb55;
    border-radius: 12px 12px 2px 12px;
    padding: 12px 16px;
    margin: 8px 0 8px 60px;
    font-size: 0.95rem;
    color: #79c0ff;
}
.bot-bubble {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px 12px 12px 2px;
    padding: 12px 16px;
    margin: 8px 60px 8px 0;
    font-size: 0.95rem;
    color: #e6edf3;
}

/* Vendor card */
.vendor-card {
    background: #0d2235;
    border: 1px solid #1f6feb;
    border-left: 4px solid #1f6feb;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 10px 0;
}
.vendor-card .vendor-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: #79c0ff;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}
.vendor-card .vendor-name {
    font-size: 1rem;
    font-weight: 600;
    color: #e6edf3;
}
.vendor-card .vendor-contact {
    font-size: 0.85rem;
    color: #8b949e;
    margin-top: 4px;
}

/* Warranty cards */
.warranty-expired {
    background: #3d1010;
    border-left: 4px solid #f85149;
    border-radius: 6px;
    padding: 12px 16px;
    margin: 6px 0;
}
.warranty-expiring {
    background: #2d1f00;
    border-left: 4px solid #e3a414;
    border-radius: 6px;
    padding: 12px 16px;
    margin: 6px 0;
}
.warranty-ok {
    background: #0d2b1e;
    border-left: 4px solid #3fb950;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 4px 0;
}

/* Alert cards */
.alert-critical {
    background: #3d1010;
    border-left: 4px solid #f85149;
    border-radius: 6px;
    padding: 12px 16px;
    margin: 6px 0;
}
.alert-high {
    background: #2d1f00;
    border-left: 4px solid #e3a414;
    border-radius: 6px;
    padding: 12px 16px;
    margin: 6px 0;
}
.alert-medium {
    background: #0d2235;
    border-left: 4px solid #388bfd;
    border-radius: 6px;
    padding: 12px 16px;
    margin: 6px 0;
}
.alert-ok {
    background: #0d2b1e;
    border-left: 4px solid #3fb950;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 4px 0;
}

.metric-box {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
}
.metric-num { font-size: 2rem; font-family: 'IBM Plex Mono', monospace; font-weight: 600; }
.metric-label { font-size: 0.8rem; color: #8b949e; margin-top: 4px; }

.stTextInput > div > div > input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 6px !important;
}
.stSelectbox > div > div {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
}
.stButton > button {
    background: #238636 !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    padding: 8px 20px !important;
}
.stButton > button:hover { background: #2ea043 !important; }

.popup-overlay {
    background: #1a0000;
    border: 2px solid #f85149;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%,100% { border-color: #f85149; }
    50%      { border-color: #ff7b7b; }
}
.warranty-popup {
    background: #1a1000;
    border: 2px solid #e3a414;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
}
.ntpc-badge {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #f0c040;
    background: #1a1500;
    border: 1px solid #f0c040;
    border-radius: 4px;
    padding: 2px 8px;
    display: inline-block;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# GEMINI API SETUP
# ─────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    st.error("""
❌ **GEMINI_API_KEY not set!**

Please stop the app and run in PowerShell:
`$env:GEMINI_API_KEY="your-key-here"`

Get a free key at: https://aistudio.google.com/app/apikey
""")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)


# ─────────────────────────────────────────────
# HELPER: PARSE VENDOR DETAILS
# ─────────────────────────────────────────────
def parse_vendor(vendor_str):
    """Split vendor details into name and contact."""
    if not vendor_str or str(vendor_str).strip() in ["", "nan"]:
        return "Not Available", ""
    v = str(vendor_str).strip()
    # Try to split on first comma
    parts = v.split(",", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return v, ""


# ─────────────────────────────────────────────
# LOAD & PROCESS DATASET
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    file_path = "NTPC_IT-PROJECT.csv"
    if not os.path.exists(file_path):
        st.error(
            "❌ Data file **'NTPC_IT-PROJECT.csv'** not found.\n\n"
            "Please place the CSV file in the **same folder** as `ntpc_helpdesk.py` and restart."
        )
        st.stop()

    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()

    # Rename columns
    df.rename(columns={
        "Maintanence Period":      "maintenance_period",
        "Maintanence Date(Last)":  "last_maintenance",
        "Crticality":              "criticality",
        "Asset_ID":                "asset_id",
        "Device_Type":             "device_type",
        "Asset_Make":              "asset_make",
        "Model_Details":           "model",
        "Purchase Date":           "purchase_date",
        "WARR END DT":             "warranty_end",
        "Vendor Details":          "vendor_details",
    }, inplace=True)

    # Parse maintenance period to days
    def period_to_days(p):
        p = str(p).strip().lower()
        if "3 month"  in p: return 90
        if "6 month"  in p: return 180
        if "12 month" in p: return 365
        return 180

    df["period_days"] = df["maintenance_period"].apply(period_to_days)

    # Parse dates
    today = pd.Timestamp(date.today())
    df["last_maintenance"] = pd.to_datetime(df["last_maintenance"], dayfirst=True, errors="coerce")
    df["purchase_date"]    = pd.to_datetime(df["purchase_date"],    dayfirst=True, errors="coerce")
    df["warranty_end"]     = pd.to_datetime(df["warranty_end"],     dayfirst=True, errors="coerce")

    # Maintenance derived columns
    df["next_maintenance"] = df["last_maintenance"] + pd.to_timedelta(df["period_days"], unit="D")
    df["days_remaining"]   = (df["next_maintenance"] - today).dt.days

    # Warranty derived columns
    df["warranty_days_left"] = (df["warranty_end"] - today).dt.days

    def warranty_status(d):
        if pd.isna(d):    return "⚪ NO DATA"
        if d < 0:         return "🔴 EXPIRED"
        if d <= 90:       return "🟠 EXPIRING SOON"
        if d <= 365:      return "🟡 VALID (<1yr)"
        return            "🟢 VALID"

    df["warranty_status"] = df["warranty_days_left"].apply(warranty_status)

    # Criticality weight
    crit_map = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
    df["crit_weight"] = df["criticality"].map(crit_map).fillna(2)

    # Urgency score
    def urgency(row):
        d = row["days_remaining"]
        if pd.isna(d): return 0
        if d <= 0:     return 999 * row["crit_weight"]
        return round(row["crit_weight"] * (1 / (d + 1)) * 1000, 2)

    df["urgency_score"] = df.apply(urgency, axis=1)

    # Maintenance status
    def maint_status(d):
        if pd.isna(d):  return "UNKNOWN"
        if d < 0:       return "🔴 OVERDUE"
        if d <= 7:      return "🔴 DUE THIS WEEK"
        if d <= 30:     return "🟠 DUE THIS MONTH"
        if d <= 60:     return "🟡 UPCOMING"
        return          "🟢 OK"

    df["status"] = df["days_remaining"].apply(maint_status)

    # Fill NaN vendor details
    df["vendor_details"] = df["vendor_details"].fillna("")

    return df.sort_values("urgency_score", ascending=False)


df = load_data()

# ─────────────────────────────────────────────
# COMMON IT ERRORS
# ─────────────────────────────────────────────
COMMON_ERRORS = [
    "System not turning on / no power",
    "Computer running very slow",
    "Blue screen / system crash (BSOD)",
    "Internet not working / no network",
    "Printer not printing / offline",
    "Printer paper jam",
    "Projector not displaying / no signal",
    "Camera / CCTV feed not showing",
    "Software not opening / crashing",
    "System overheating / fan noise",
    "Mouse / keyboard not working",
    "Monitor no display / blank screen",
    "Virus / malware suspected",
    "Server not responding",
    "Photocopier error / not working",
    "Other (type below)",
]


# ─────────────────────────────────────────────
# VENDOR CARD RENDERER
# ─────────────────────────────────────────────
def show_vendor_card(asset_row, context="solution"):
    """Render a vendor info card for the given asset row."""
    vendor_raw = asset_row.get("vendor_details", "")
    vendor_name, vendor_contact = parse_vendor(vendor_raw)
    asset_id   = asset_row.get("asset_id", "N/A")
    device     = asset_row.get("device_type", "N/A")
    warr_status= asset_row.get("warranty_status", "⚪ NO DATA")
    warr_days  = asset_row.get("warranty_days_left", None)

    warr_str = ""
    if pd.notna(warr_days):
        if warr_days < 0:
            warr_str = f"<span style='color:#f85149'>Expired {abs(int(warr_days))} days ago</span>"
        else:
            warr_str = f"<span style='color:#3fb950'>Valid for {int(warr_days)} more days</span>"
    else:
        warr_str = "<span style='color:#8b949e'>No warranty data</span>"

    st.markdown(f"""
<div class="vendor-card">
  <div class="vendor-title">📞 Vendor & Warranty Details — {asset_id} ({device})</div>
  <div class="vendor-name">🏢 {vendor_name}</div>
  <div class="vendor-contact">📱 {vendor_contact if vendor_contact else 'Contact not available'}</div>
  <div class="vendor-contact" style="margin-top:6px">🛡️ Warranty: {warr_status} &nbsp;|&nbsp; {warr_str}</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# AI SOLUTION GENERATOR
# ─────────────────────────────────────────────
def get_ai_solution(error_desc: str, device_info: dict) -> str:
    device_context = ""
    if device_info:
        warr_days = device_info.get("warranty_days_left", None)
        warr_note = ""
        if pd.notna(warr_days) if not isinstance(warr_days, str) else False:
            if warr_days < 0:
                warr_note = f"WARRANTY EXPIRED {abs(int(warr_days))} days ago — escalate to vendor!"
            elif warr_days <= 90:
                warr_note = f"WARRANTY EXPIRING in {int(warr_days)} days — contact vendor soon."
            else:
                warr_note = f"Warranty valid for {int(warr_days)} more days."

        vendor_raw = device_info.get("vendor_details", "")
        vendor_name, vendor_contact = parse_vendor(vendor_raw)

        device_context = f"""
Device Information from NTPC Asset Register:
- Asset ID        : {device_info.get('asset_id', 'N/A')}
- Device Type     : {device_info.get('device_type', 'N/A')}
- Make/Brand      : {device_info.get('asset_make', 'N/A')}
- Model           : {device_info.get('model', 'N/A')}
- Purchase Date   : {device_info.get('purchase_date', 'N/A')}
- Criticality     : {device_info.get('criticality', 'N/A')}
- Last Maintenance: {device_info.get('last_maintenance', 'N/A')}
- Next Due Date   : {device_info.get('next_maintenance', 'N/A')}
- Days Until Due  : {device_info.get('days_remaining', 'N/A')} days
- Warranty Status : {device_info.get('warranty_status', 'N/A')} — {warr_note}
- Vendor          : {vendor_name} | {vendor_contact}
"""
    else:
        device_context = "Device not found in NTPC asset register. Providing general advice."

    prompt = f"""You are an expert IT helpdesk assistant for NTPC (National Thermal Power Corporation),
a major Indian government power company. You are helping an IT staff member diagnose and fix a problem.

{device_context}

Reported Problem: {error_desc}

Today's Date: {date.today().strftime('%d %B %Y')}

Please provide a structured response with these exact sections:

## 🔍 Problem Diagnosis
Brief analysis of what is likely causing this issue, considering the device age and maintenance history.

## 🛠️ Step-by-Step Fix
Numbered steps to resolve the issue (be specific, practical, beginner-friendly).

## 🔧 Maintenance Required?
State clearly: YES or NO. If YES, explain what maintenance is needed and how urgent.

## 🧹 Cleaning Required?
State clearly: YES or NO. If YES, explain what cleaning steps are recommended.

## ⚠️ Preventive Measures
3-4 bullet points to prevent this issue in future.

## 📞 Escalation
When should this be escalated to vendor support? Note any warranty considerations.

Keep the tone professional but simple. Use plain English."""

    try:
        model    = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"""## ⚠️ AI Service Unavailable

The AI assistant is temporarily offline. Here are general steps:

**For '{error_desc}':**
1. Restart the device first — resolves ~60% of issues
2. Check all cable connections
3. Check if other devices have the same issue (network problem vs device problem)
4. Check event logs if it's a PC/Server
5. Contact vendor support if issue persists

**Error details:** {str(e)}"""


# ─────────────────────────────────────────────
# MAINTENANCE ALERTS POPUP
# ─────────────────────────────────────────────
def show_maintenance_alerts():
    urgent = df[df["days_remaining"] <= 7].copy()
    if urgent.empty:
        return
    overdue   = urgent[urgent["days_remaining"] < 0]
    this_week = urgent[urgent["days_remaining"] >= 0]

    st.markdown('<div class="popup-overlay">', unsafe_allow_html=True)
    st.markdown("### 🚨 URGENT MAINTENANCE ALERTS")

    if not overdue.empty:
        st.markdown(f"**{len(overdue)} device(s) are OVERDUE for maintenance!**")
        for _, row in overdue.iterrows():
            vendor_name, vendor_contact = parse_vendor(row["vendor_details"])
            st.markdown(f"""
<div class="alert-critical">
<strong>🔴 OVERDUE: {row['asset_id']}</strong> — {row['device_type']} ({row['asset_make']} {row['model']})<br>
<small>Overdue by <strong>{abs(int(row['days_remaining']))} days</strong> |
Criticality: <strong>{row['criticality']}</strong> |
Last maintained: {row['last_maintenance'].strftime('%d %b %Y') if pd.notna(row['last_maintenance']) else 'Unknown'}</small><br>
<small>📞 Vendor: <strong>{vendor_name}</strong> {(' | ' + vendor_contact) if vendor_contact else ''}</small>
</div>""", unsafe_allow_html=True)

    if not this_week.empty:
        st.markdown(f"**{len(this_week)} device(s) due within 7 days:**")
        for _, row in this_week.iterrows():
            vendor_name, vendor_contact = parse_vendor(row["vendor_details"])
            st.markdown(f"""
<div class="alert-high">
<strong>🟠 DUE SOON: {row['asset_id']}</strong> — {row['device_type']} ({row['asset_make']})<br>
<small>Due in <strong>{int(row['days_remaining'])} days</strong> on {row['next_maintenance'].strftime('%d %b %Y')} |
Criticality: <strong>{row['criticality']}</strong></small><br>
<small>📞 Vendor: <strong>{vendor_name}</strong> {(' | ' + vendor_contact) if vendor_contact else ''}</small>
</div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# WARRANTY ALERTS POPUP  ← NEW
# ─────────────────────────────────────────────
def show_warranty_alerts():
    expired  = df[df["warranty_days_left"] < 0].copy()
    expiring = df[(df["warranty_days_left"] >= 0) & (df["warranty_days_left"] <= 90)].copy()

    if expired.empty and expiring.empty:
        return

    st.markdown('<div class="warranty-popup">', unsafe_allow_html=True)
    st.markdown("### 🛡️ WARRANTY ALERTS")

    if not expired.empty:
        st.markdown(f"**{len(expired)} device(s) have EXPIRED warranties!**")
        for _, row in expired.iterrows():
            vendor_name, vendor_contact = parse_vendor(row["vendor_details"])
            exp_date = row["warranty_end"].strftime('%d %b %Y') if pd.notna(row["warranty_end"]) else "Unknown"
            st.markdown(f"""
<div class="warranty-expired">
<strong>🔴 WARRANTY EXPIRED: {row['asset_id']}</strong> — {row['device_type']} ({row['asset_make']} {row['model']})<br>
<small>Expired on: <strong>{exp_date}</strong> ({abs(int(row['warranty_days_left']))} days ago) |
Criticality: <strong>{row['criticality']}</strong></small><br>
<small>📞 Vendor: <strong>{vendor_name}</strong> {(' | ' + vendor_contact) if vendor_contact else ''}</small>
</div>""", unsafe_allow_html=True)

    if not expiring.empty:
        st.markdown(f"**{len(expiring)} device(s) warranty expiring within 90 days:**")
        for _, row in expiring.iterrows():
            vendor_name, vendor_contact = parse_vendor(row["vendor_details"])
            exp_date = row["warranty_end"].strftime('%d %b %Y') if pd.notna(row["warranty_end"]) else "Unknown"
            st.markdown(f"""
<div class="warranty-expiring">
<strong>🟠 EXPIRING SOON: {row['asset_id']}</strong> — {row['device_type']} ({row['asset_make']} {row['model']})<br>
<small>Expires on: <strong>{exp_date}</strong> (in {int(row['warranty_days_left'])} days) |
Criticality: <strong>{row['criticality']}</strong></small><br>
<small>📞 Vendor: <strong>{vendor_name}</strong> {(' | ' + vendor_contact) if vendor_contact else ''}</small>
</div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="ntpc-badge">⚡ NTPC IT DIVISION</div>', unsafe_allow_html=True)
    st.markdown("## IT Helpdesk System")
    st.markdown("---")

    page = st.radio(
        "Navigate to:",
        ["💬 IT Helpdesk Chatbot", "🔔 Maintenance Dashboard"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("**🔍 Quick Device Lookup**")
    search_id = st.text_input("Enter Asset ID (e.g. PC_101)", placeholder="PC_101")
    if search_id:
        match = df[df["asset_id"].str.upper() == search_id.strip().upper()]
        if not match.empty:
            r = match.iloc[0]
            st.success(f"**{r['asset_id']}** found!")
            st.caption(f"{r['device_type']} | {r['asset_make']} {r['model']}")
            st.caption(f"Maintenance: {r['status']}")
            st.caption(f"Warranty: {r['warranty_status']}")
            st.caption(f"Criticality: {r['criticality']}")
            days = int(r['days_remaining']) if pd.notna(r['days_remaining']) else 'N/A'
            if isinstance(days, (int, float)) and days < 0:
                st.error(f"Maintenance overdue by {abs(int(days))} days!")
            elif isinstance(days, (int, float)) and days <= 30:
                st.warning(f"Maintenance due in {int(days)} days")
            # Warranty quick status
            wdays = r['warranty_days_left']
            if pd.notna(wdays):
                if wdays < 0:
                    st.error(f"Warranty expired {abs(int(wdays))} days ago!")
                elif wdays <= 90:
                    st.warning(f"Warranty expiring in {int(wdays)} days!")
            # Show vendor
            vendor_name, vendor_contact = parse_vendor(r['vendor_details'])
            st.caption(f"📞 {vendor_name}")
            if vendor_contact:
                st.caption(f"   {vendor_contact}")
        else:
            st.warning("Asset ID not found")

    st.markdown("---")
    st.caption(f"Dataset: {len(df)} assets loaded")
    st.caption(f"Last refresh: {datetime.now().strftime('%d %b %Y %H:%M')}")


# ─────────────────────────────────────────────
# PAGE 1 — IT HELPDESK CHATBOT
# ─────────────────────────────────────────────
if "💬 IT Helpdesk Chatbot" in page:

    st.markdown("# ⚡ NTPC IT Helpdesk")
    st.markdown("*AI-powered troubleshooting assistant — NTPC IT Division*")

    # Show both alert popups
    show_maintenance_alerts()
    show_warranty_alerts()

    st.markdown("---")

    # Session state
    if "step"           not in st.session_state: st.session_state.step = 1
    if "error_desc"     not in st.session_state: st.session_state.error_desc = ""
    if "selected_asset" not in st.session_state: st.session_state.selected_asset = None
    if "chat_history"   not in st.session_state: st.session_state.chat_history = []
    if "solution_shown" not in st.session_state: st.session_state.solution_shown = False

    # Display chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-bubble">👤 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-bubble">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

    # ── STEP 1: Select error ──────────────────────────────────
    if st.session_state.step == 1:
        st.markdown('<div class="bot-bubble">🤖 <strong>Welcome to NTPC IT Helpdesk!</strong><br>What problem are you facing? Please select from the list or describe it below.</div>', unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])
        with col1:
            error_choice = st.selectbox("Select common error:",
                ["-- Select an issue --"] + COMMON_ERRORS,
                label_visibility="collapsed")
        with col2:
            if st.button("Next →", key="btn_step1"):
                if error_choice != "-- Select an issue --" and error_choice != "Other (type below)":
                    st.session_state.error_desc = error_choice
                    st.session_state.chat_history.append({"role": "user",     "content": f"My problem: {error_choice}"})
                    st.session_state.chat_history.append({"role": "assistant","content": "Got it! Now please tell me — **which device is having this issue?** Enter the Asset ID or select device type."})
                    st.session_state.step = 2
                    st.rerun()
                else:
                    st.warning("Please select an issue above")

        custom_error = st.text_input("Or describe your issue:", placeholder="e.g. My screen flickers when I open Excel")
        if custom_error and st.button("Submit custom issue", key="btn_custom"):
            st.session_state.error_desc = custom_error
            st.session_state.chat_history.append({"role": "user",     "content": f"My problem: {custom_error}"})
            st.session_state.chat_history.append({"role": "assistant","content": "Got it! Now please tell me — **which device is having this issue?**"})
            st.session_state.step = 2
            st.rerun()

    # ── STEP 2: Select device ────────────────────────────────
    elif st.session_state.step == 2:
        st.markdown("**Step 2: Identify your device**")
        col1, col2 = st.columns(2)

        with col1:
            device_type_filter = st.selectbox("Device Type (optional filter):",
                ["All"] + sorted(df["device_type"].unique().tolist()))

        filtered_df = df if device_type_filter == "All" else df[df["device_type"] == device_type_filter]
        asset_options = [f"{row['asset_id']} — {row['device_type']} ({row['asset_make']} {row['model']})"
                         for _, row in filtered_df.iterrows()]

        with col2:
            selected_asset_str = st.selectbox("Select your device:", ["-- Select --"] + asset_options)

        col3, col4 = st.columns(2)
        with col3:
            if st.button("Get Solution ✓", key="btn_step2"):
                if selected_asset_str != "-- Select --":
                    asset_id = selected_asset_str.split(" — ")[0]
                    row = df[df["asset_id"] == asset_id].iloc[0]
                    st.session_state.selected_asset = row.to_dict()
                    st.session_state.chat_history.append({"role": "user",
                        "content": f"My device: {asset_id} — {row['device_type']} ({row['asset_make']} {row['model']})"})
                    st.session_state.chat_history.append({"role": "assistant",
                        "content": "Found your device in the NTPC asset register ✅. Analysing the issue and generating a customised solution..."})
                    st.session_state.step = 3
                    st.rerun()
                else:
                    st.warning("Please select your device")
        with col4:
            if st.button("Device not in list", key="btn_no_asset"):
                st.session_state.selected_asset = {}
                st.session_state.chat_history.append({"role": "user",     "content": "My device is not in the asset register."})
                st.session_state.chat_history.append({"role": "assistant","content": "No problem! I'll give you general troubleshooting advice."})
                st.session_state.step = 3
                st.rerun()

    # ── STEP 3: Show AI solution + vendor card ────────────────
    elif st.session_state.step == 3 and not st.session_state.solution_shown:

        with st.spinner("🤖 Analysing issue and generating solution..."):
            solution = get_ai_solution(
                st.session_state.error_desc,
                st.session_state.selected_asset
            )

        # Maintenance warning
        if st.session_state.selected_asset:
            asset = st.session_state.selected_asset
            days  = asset.get("days_remaining")
            if isinstance(days, (int, float)) and pd.notna(days) and days <= 30:
                st.warning(f"⚠️ This device ({asset.get('asset_id')}) is due for maintenance in **{int(days)} days**.")

        # AI Solution
        st.markdown('<div class="bot-bubble">', unsafe_allow_html=True)
        st.markdown(solution)
        st.markdown('</div>', unsafe_allow_html=True)
        st.session_state.chat_history.append({"role": "assistant", "content": solution})

        # ── VENDOR CARD after solution ← NEW ──────────────────
        if st.session_state.selected_asset:
            show_vendor_card(st.session_state.selected_asset, context="solution")

        st.session_state.solution_shown = True

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Issue", key="btn_reset"):
                for k in ["step","error_desc","selected_asset","chat_history","solution_shown"]:
                    del st.session_state[k]
                st.rerun()
        with col2:
            if st.button("📋 Ask Follow-up", key="btn_followup"):
                st.session_state.step = 4
                st.rerun()

    elif st.session_state.step == 3 and st.session_state.solution_shown:
        # Show vendor card again after rerun
        if st.session_state.selected_asset:
            show_vendor_card(st.session_state.selected_asset)
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Issue", key="btn_reset2"):
                for k in ["step","error_desc","selected_asset","chat_history","solution_shown"]:
                    del st.session_state[k]
                st.rerun()
        with col2:
            if st.button("📋 Ask Follow-up", key="btn_followup2"):
                st.session_state.step = 4
                st.rerun()

    # ── STEP 4: Follow-up ────────────────────────────────────
    elif st.session_state.step == 4:
        if st.session_state.selected_asset:
            show_vendor_card(st.session_state.selected_asset)
        follow_up = st.text_input("Ask a follow-up question:", placeholder="e.g. How do I update the BIOS?")
        if follow_up and st.button("Send", key="btn_send_followup"):
            with st.spinner("Thinking..."):
                combined = f"Original issue: {st.session_state.error_desc}\nFollow-up: {follow_up}"
                response = get_ai_solution(combined, st.session_state.selected_asset)
            st.session_state.chat_history.append({"role": "user",     "content": follow_up})
            st.session_state.chat_history.append({"role": "assistant","content": response})
            st.rerun()
        if st.button("🔄 Start New Issue", key="btn_new"):
            for k in ["step","error_desc","selected_asset","chat_history","solution_shown"]:
                del st.session_state[k]
            st.rerun()


# ─────────────────────────────────────────────
# PAGE 2 — MAINTENANCE DASHBOARD
# ─────────────────────────────────────────────
elif "🔔 Maintenance Dashboard" in page:

    st.markdown("# 🔔 Maintenance Dashboard")
    st.markdown("*Real-time view of all NTPC IT assets and their maintenance & warranty status*")

    show_maintenance_alerts()
    show_warranty_alerts()

    st.markdown("---")

    # ── Summary metrics ────────────────────────────────────────
    overdue_count    = len(df[df["days_remaining"] < 0])
    thisweek_count   = len(df[(df["days_remaining"] >= 0) & (df["days_remaining"] <= 7)])
    thismonth_count  = len(df[(df["days_remaining"] > 7)  & (df["days_remaining"] <= 30)])
    ok_count         = len(df[df["days_remaining"] > 30])
    warr_exp_count   = len(df[df["warranty_days_left"] < 0])
    warr_soon_count  = len(df[(df["warranty_days_left"] >= 0) & (df["warranty_days_left"] <= 90)])

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.markdown(f'<div class="metric-box"><div class="metric-num" style="color:#f85149">{overdue_count}</div><div class="metric-label">MAINT. OVERDUE</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-box"><div class="metric-num" style="color:#e3a414">{thisweek_count}</div><div class="metric-label">DUE THIS WEEK</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-box"><div class="metric-num" style="color:#388bfd">{thismonth_count}</div><div class="metric-label">DUE THIS MONTH</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-box"><div class="metric-num" style="color:#3fb950">{ok_count}</div><div class="metric-label">MAINT. OK</div></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="metric-box"><div class="metric-num" style="color:#f85149">{warr_exp_count}</div><div class="metric-label">WARR. EXPIRED</div></div>', unsafe_allow_html=True)
    with col6:
        st.markdown(f'<div class="metric-box"><div class="metric-num" style="color:#e3a414">{warr_soon_count}</div><div class="metric-label">WARR. EXPIRING</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Filters ────────────────────────────────────────────────
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        filter_status = st.selectbox("Maintenance Status:",
            ["All", "🔴 OVERDUE", "🔴 DUE THIS WEEK", "🟠 DUE THIS MONTH", "🟡 UPCOMING", "🟢 OK"])
    with col_f2:
        filter_type = st.selectbox("Device Type:",
            ["All"] + sorted(df["device_type"].unique().tolist()))
    with col_f3:
        filter_crit = st.selectbox("Criticality:",
            ["All", "Critical", "High", "Medium", "Low"])
    with col_f4:
        filter_warr = st.selectbox("Warranty Status:",
            ["All", "🔴 EXPIRED", "🟠 EXPIRING SOON", "🟡 VALID (<1yr)", "🟢 VALID", "⚪ NO DATA"])

    # Apply filters
    filtered = df.copy()
    if filter_status != "All":
        filtered = filtered[filtered["status"] == filter_status]
    if filter_type != "All":
        filtered = filtered[filtered["device_type"] == filter_type]
    if filter_crit != "All":
        filtered = filtered[filtered["criticality"] == filter_crit]
    if filter_warr != "All":
        filtered = filtered[filtered["warranty_status"] == filter_warr]

    st.markdown(f"**Showing {len(filtered)} assets** (sorted by urgency)")

    # ── Asset cards with vendor details ── NEW ────────────────
    for _, row in filtered.iterrows():
        days = row["days_remaining"]
        days_str = f"{int(days)} days" if pd.notna(days) else "Unknown"

        if pd.notna(days) and days < 0:
            card_class = "alert-critical"
        elif pd.notna(days) and days <= 7:
            card_class = "alert-high"
        elif pd.notna(days) and days <= 30:
            card_class = "alert-medium"
        else:
            card_class = "alert-ok"

        next_date  = row["next_maintenance"].strftime("%d %b %Y") if pd.notna(row["next_maintenance"]) else "N/A"
        warr_date  = row["warranty_end"].strftime("%d %b %Y")     if pd.notna(row["warranty_end"])     else "N/A"
        vendor_name, vendor_contact = parse_vendor(row["vendor_details"])

        st.markdown(f"""
<div class="{card_class}">
<strong>{row['status']} &nbsp;|&nbsp; {row['asset_id']}</strong> — {row['device_type']}
<span style="color:#8b949e;font-size:0.85rem"> {row['asset_make']} {row['model']}</span><br>
<small>
Next maintenance: <strong>{next_date}</strong> &nbsp;|&nbsp;
Days remaining: <strong>{days_str}</strong> &nbsp;|&nbsp;
Criticality: <strong>{row['criticality']}</strong> &nbsp;|&nbsp;
Urgency: <strong>{row['urgency_score']:.1f}</strong>
</small><br>
<small>
🛡️ Warranty: <strong>{row['warranty_status']}</strong> (expires: {warr_date}) &nbsp;|&nbsp;
📞 <strong>{vendor_name}</strong>{(' — ' + vendor_contact) if vendor_contact else ''}
</small>
</div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Full data table
    with st.expander("📊 View Full Asset Table"):
        display_cols = ["asset_id","device_type","asset_make","model","criticality",
                        "last_maintenance","next_maintenance","days_remaining","status",
                        "warranty_end","warranty_status","vendor_details","urgency_score"]
        st.dataframe(
            filtered[display_cols].rename(columns={
                "asset_id":"ID","device_type":"Type","asset_make":"Brand","model":"Model",
                "criticality":"Criticality","last_maintenance":"Last Maintained",
                "next_maintenance":"Next Due","days_remaining":"Days Left","status":"Maint. Status",
                "warranty_end":"Warranty End","warranty_status":"Warranty Status",
                "vendor_details":"Vendor","urgency_score":"Urgency Score"
            }),
            use_container_width=True, height=400
        )
