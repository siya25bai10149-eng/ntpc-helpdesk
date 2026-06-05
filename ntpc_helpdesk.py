"""
NTPC IT Helpdesk Chatbot + Maintenance Alert System
====================================================
Internship Project | NTPC IT Division
Built with: Python, Streamlit, Anthropic Claude API, Pandas

Features:
  1. AI-powered chatbot for IT troubleshooting
  2. Step-by-step guided diagnosis (error → device → solution)
  3. Device-specific solutions using real NTPC asset data
  4. Maintenance dashboard with urgency scoring
  5. Critical maintenance popup alerts

Fixes applied:
  [FIX 1] Removed unused 'import json'
  [FIX 2] Removed unnecessary f-prefix on plain string (line ~545)
  [FIX 3] isinstance(days, (int, float)) used consistently in sidebar
           to handle numpy.int64 returned by pandas .dt.days
  [FIX 4] load_data() now checks file existence before reading,
           shows a clear error and stops instead of crashing
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime, date
import anthropic
# ✅ FIX 1: Removed unused 'import json'

# ─────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NTPC IT Helpdesk",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS  – clean industrial/utility theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

/* ---- Base ---- */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0d1117;
    color: #e6edf3;
}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background: #161b22;
    border-right: 1px solid #30363d;
}

/* ---- Headers ---- */
h1, h2, h3 { font-family: 'IBM Plex Mono', monospace; }

/* ---- Chat bubbles ---- */
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
.bot-bubble strong { color: #f0c040; }

/* ---- Alert cards ---- */
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

/* ---- Metric boxes ---- */
.metric-box {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
}
.metric-num { font-size: 2rem; font-family: 'IBM Plex Mono', monospace; font-weight: 600; }
.metric-label { font-size: 0.8rem; color: #8b949e; margin-top: 4px; }

/* ---- Input ---- */
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

/* ---- Buttons ---- */
.stButton > button {
    background: #238636 !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    padding: 8px 20px !important;
    transition: background 0.2s !important;
}
.stButton > button:hover { background: #2ea043 !important; }

/* ---- Popup overlay ---- */
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

/* ---- NTPC badge ---- */
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
# LOAD & PROCESS DATASET
# ─────────────────────────────────────────────
@st.cache_data  # cache so file is read only once
def load_data():
    """
    Load the NTPC IT asset Excel file and compute:
      - next_maintenance  : date when maintenance is due
      - days_remaining    : days until (or since) maintenance
      - urgency_score     : composite score for prioritisation
      - status            : OVERDUE / DUE SOON / UPCOMING / OK
    """
    # ✅ FIX 4: Check file existence before reading — prevents raw crash
    file_path = "NTPC_IT-PROJECT.xlsx"
    if not os.path.exists(file_path):
        st.error(
            "❌ Data file **'NTPC_IT-PROJECT.xlsx'** not found.\n\n"
            "Please place the Excel file in the **same folder** as `ntpc_helpdesk.py` and restart the app."
        )
        st.stop()

    import os, glob
# Find the Excel file automatically regardless of exact name
excel_files = glob.glob("*.xlsx") + glob.glob("/app/**/*.xlsx", recursive=True)
excel_path = excel_files[0] if excel_files else "NTPC_IT-PROJECT.xlsx"
df = pd.read_excel(excel_path)

    # ── Clean column names ──────────────────────────────────────
    df.columns = df.columns.str.strip()
    df.rename(columns={
        "Maintanence Period":      "maintenance_period",
        "Maintanence Date(Last)":  "last_maintenance",
        "Crticality":              "criticality",
        "Asset_ID":                "asset_id",
        "Device_Type":             "device_type",
        "Asset_Make":              "asset_make",
        "Model_Details":           "model",
        "Purchase Date":           "purchase_date",
    }, inplace=True)

    # ── Parse periods to days ───────────────────────────────────
    def period_to_days(p):
        p = str(p).strip().lower()
        if "3 month"  in p: return 90
        if "6 month"  in p: return 180
        if "12 month" in p: return 365
        return 180  # default fallback

    df["period_days"] = df["maintenance_period"].apply(period_to_days)

    # ── Convert date columns ────────────────────────────────────
    df["last_maintenance"] = pd.to_datetime(df["last_maintenance"], errors="coerce")

    today = pd.Timestamp(date.today())

    # ── Derived columns ─────────────────────────────────────────
    df["next_maintenance"] = df["last_maintenance"] + pd.to_timedelta(df["period_days"], unit="D")
    df["days_remaining"]   = (df["next_maintenance"] - today).dt.days

    # ── Criticality weight (for urgency score) ──────────────────
    crit_map = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
    df["crit_weight"] = df["criticality"].map(crit_map).fillna(2)

    # ── Urgency score: higher = needs attention sooner ──────────
    # Formula: criticality_weight × (1 / (days_remaining + 1))
    # Capped at 999 for overdue items
    def urgency(row):
        d = row["days_remaining"]
        if pd.isna(d): return 0
        if d <= 0:     return 999 * row["crit_weight"]  # overdue!
        return round(row["crit_weight"] * (1 / (d + 1)) * 1000, 2)

    df["urgency_score"] = df.apply(urgency, axis=1)

    # ── Status label ────────────────────────────────────────────
    def status(d):
        if pd.isna(d):  return "UNKNOWN"
        if d < 0:       return "🔴 OVERDUE"
        if d <= 7:      return "🔴 DUE THIS WEEK"
        if d <= 30:     return "🟠 DUE THIS MONTH"
        if d <= 60:     return "🟡 UPCOMING"
        return          "🟢 OK"

    df["status"] = df["days_remaining"].apply(status)

    return df.sort_values("urgency_score", ascending=False)


# Load dataset
df = load_data()


# ─────────────────────────────────────────────
# COMMON IT ERRORS  (used in chatbot quick-pick)
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
# AI SOLUTION GENERATOR  (calls Claude API)
# ─────────────────────────────────────────────
def get_ai_solution(error_desc: str, device_info: dict) -> str:
    """
    Sends error + device context to Claude API.
    Returns a structured troubleshooting response.
    """

    # Build a rich context string from device data
    device_context = ""
    if device_info:
        device_context = f"""
Device Information from NTPC Asset Register:
- Asset ID      : {device_info.get('asset_id', 'N/A')}
- Device Type   : {device_info.get('device_type', 'N/A')}
- Make/Brand    : {device_info.get('asset_make', 'N/A')}
- Model         : {device_info.get('model', 'N/A')}
- Purchase Date : {device_info.get('purchase_date', 'N/A')}
- Criticality   : {device_info.get('criticality', 'N/A')}
- Last Maintenance : {device_info.get('last_maintenance', 'N/A')}
- Next Due Date    : {device_info.get('next_maintenance', 'N/A')}
- Days Until Due   : {device_info.get('days_remaining', 'N/A')} days
"""
    else:
        device_context = "Device not found in NTPC asset register. Giving general advice."

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
When should this be escalated to senior IT or vendor support?

Keep the tone professional but simple. Use plain English. No jargon unless necessary."""

    try:
        # Call Anthropic API
        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-opus-4-5-20251101",   # ✅ Full model string for reliability
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    except Exception as e:
        # Graceful fallback if API fails
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
def show_critical_alerts():
    """
    Shows a prominent popup/banner for overdue and this-week-due devices.
    Sorted by urgency score — most critical first.
    """
    # Filter only urgent items
    urgent = df[df["days_remaining"] <= 7].copy()

    if urgent.empty:
        return  # No urgent items, don't show popup

    overdue   = urgent[urgent["days_remaining"] < 0]
    this_week = urgent[urgent["days_remaining"] >= 0]

    st.markdown('<div class="popup-overlay">', unsafe_allow_html=True)
    st.markdown("### 🚨 URGENT MAINTENANCE ALERTS")

    if not overdue.empty:
        st.markdown(f"**{len(overdue)} device(s) are OVERDUE for maintenance!**")
        for _, row in overdue.iterrows():
            st.markdown(f"""
<div class="alert-critical">
<strong>🔴 OVERDUE: {row['asset_id']}</strong> — {row['device_type']} ({row['asset_make']} {row['model']})<br>
<small>Overdue by <strong>{abs(int(row['days_remaining']))} days</strong> | 
Criticality: <strong>{row['criticality']}</strong> | 
Last maintained: {row['last_maintenance'].strftime('%d %b %Y') if pd.notna(row['last_maintenance']) else 'Unknown'}</small>
</div>""", unsafe_allow_html=True)

    if not this_week.empty:
        st.markdown(f"**{len(this_week)} device(s) due within 7 days:**")
        for _, row in this_week.iterrows():
            st.markdown(f"""
<div class="alert-high">
<strong>🟠 DUE SOON: {row['asset_id']}</strong> — {row['device_type']} ({row['asset_make']})<br>
<small>Due in <strong>{int(row['days_remaining'])} days</strong> on {row['next_maintenance'].strftime('%d %b %Y')} | 
Criticality: <strong>{row['criticality']}</strong></small>
</div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SIDEBAR  – navigation + device search
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="ntpc-badge">⚡ NTPC IT DIVISION</div>', unsafe_allow_html=True)
    st.markdown("## IT Helpdesk System")
    st.markdown("---")

    # Navigation
    page = st.radio(
        "Navigate to:",
        ["💬 IT Helpdesk Chatbot", "🔔 Maintenance Dashboard"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Quick device lookup
    st.markdown("**🔍 Quick Device Lookup**")
    search_id = st.text_input("Enter Asset ID (e.g. PC_101)", placeholder="PC_101")
    if search_id:
        match = df[df["asset_id"].str.upper() == search_id.strip().upper()]
        if not match.empty:
            r = match.iloc[0]
            st.success(f"**{r['asset_id']}** found!")
            st.caption(f"{r['device_type']} | {r['asset_make']} {r['model']}")
            st.caption(f"Status: {r['status']}")
            st.caption(f"Criticality: {r['criticality']}")
            # ✅ FIX 3: Use isinstance(days, (int, float)) to safely handle
            #    numpy.int64 which pandas .dt.days returns — plain `int` check
            #    can silently fail with numpy types on some pandas versions.
            days = int(r['days_remaining']) if pd.notna(r['days_remaining']) else 'N/A'
            if isinstance(days, (int, float)) and days < 0:
                st.error(f"Overdue by {abs(int(days))} days!")
            elif isinstance(days, (int, float)) and days <= 30:
                st.warning(f"Due in {int(days)} days")
            else:
                st.info(f"Next due in {days} days")
        else:
            st.warning("Asset ID not found")

    st.markdown("---")
    st.caption(f"Dataset: {len(df)} assets loaded")
    st.caption(f"Last refresh: {datetime.now().strftime('%d %b %Y %H:%M')}")


# ─────────────────────────────────────────────
# PAGE 1 — IT HELPDESK CHATBOT
# ─────────────────────────────────────────────
if "💬 IT Helpdesk Chatbot" in page:

    # ── Title ──────────────────────────────────────────────────
    st.markdown("# ⚡ NTPC IT Helpdesk")
    st.markdown("*AI-powered troubleshooting assistant — NTPC IT Division*")

    # Show critical alerts at top of chatbot page too
    show_critical_alerts()

    st.markdown("---")

    # ── Session state for multi-step flow ──────────────────────
    if "step"          not in st.session_state: st.session_state.step = 1
    if "error_desc"    not in st.session_state: st.session_state.error_desc = ""
    if "selected_asset"not in st.session_state: st.session_state.selected_asset = None
    if "chat_history"  not in st.session_state: st.session_state.chat_history = []
    if "solution_shown"not in st.session_state: st.session_state.solution_shown = False

    # ── Display chat history ───────────────────────────────────
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-bubble">👤 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-bubble">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────
    # STEP 1 — Ask what error the user is facing
    # ──────────────────────────────────────────────────────────
    if st.session_state.step == 1:
        st.markdown('<div class="bot-bubble">🤖 <strong>Welcome to NTPC IT Helpdesk!</strong><br>What problem are you facing? Please select from the list or describe it below.</div>', unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])

        with col1:
            error_choice = st.selectbox(
                "Select common error:",
                ["-- Select an issue --"] + COMMON_ERRORS,
                label_visibility="collapsed"
            )

        with col2:
            if st.button("Next →", key="btn_step1"):
                if error_choice != "-- Select an issue --" and error_choice != "Other (type below)":
                    st.session_state.error_desc = error_choice
                    st.session_state.chat_history.append({"role": "user",    "content": f"My problem: {error_choice}"})
                    st.session_state.chat_history.append({"role": "assistant","content": "Got it! Now please tell me — **which device is having this issue?** Enter the Asset ID (e.g. PC_101) or select the device type."})
                    st.session_state.step = 2
                    st.rerun()
                else:
                    st.warning("Please select an issue above")

        # Free-text fallback
        custom_error = st.text_input("Or describe your issue:", placeholder="e.g. My screen flickers when I open Excel")
        if custom_error and st.button("Submit custom issue", key="btn_custom"):
            st.session_state.error_desc = custom_error
            st.session_state.chat_history.append({"role": "user",    "content": f"My problem: {custom_error}"})
            st.session_state.chat_history.append({"role": "assistant","content": "Got it! Now please tell me — **which device is having this issue?** Enter the Asset ID or select device type below."})
            st.session_state.step = 2
            st.rerun()

    # ──────────────────────────────────────────────────────────
    # STEP 2 — Ask which device
    # ──────────────────────────────────────────────────────────
    elif st.session_state.step == 2:

        st.markdown("**Step 2: Identify your device**")

        col1, col2 = st.columns(2)

        with col1:
            # Filter by device type first (optional)
            device_type_filter = st.selectbox(
                "Device Type (optional filter):",
                ["All"] + sorted(df["device_type"].unique().tolist())
            )

        # Filter asset list
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
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": f"My device: {asset_id} — {row['device_type']} ({row['asset_make']} {row['model']})"
                    })
                    # ✅ FIX 2: Removed unnecessary f-prefix — no {variables} inside this string
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": "Found your device in the NTPC asset register ✅. Analysing the issue and generating a customised solution..."
                    })
                    st.session_state.step = 3
                    st.rerun()
                else:
                    st.warning("Please select your device")

        with col4:
            if st.button("Device not in list", key="btn_no_asset"):
                st.session_state.selected_asset = {}
                st.session_state.chat_history.append({"role": "user",     "content": "My device is not in the asset register."})
                st.session_state.chat_history.append({"role": "assistant","content": "No problem! I'll give you general troubleshooting advice for this type of issue."})
                st.session_state.step = 3
                st.rerun()

    # ──────────────────────────────────────────────────────────
    # STEP 3 — Generate and show AI solution
    # ──────────────────────────────────────────────────────────
    elif st.session_state.step == 3 and not st.session_state.solution_shown:

        with st.spinner("🤖 Analysing issue and generating solution..."):
            solution = get_ai_solution(
                st.session_state.error_desc,
                st.session_state.selected_asset
            )

        # Show device context card if device was found
        if st.session_state.selected_asset:
            asset = st.session_state.selected_asset
            days  = asset.get("days_remaining")

            # Maintenance warning alongside solution
            if isinstance(days, (int, float)) and days <= 30:
                st.warning(f"⚠️ Note: This device ({asset.get('asset_id')}) is due for maintenance in **{int(days)} days**. The issue you're facing may be related to overdue maintenance.")

        # Display solution
        st.markdown('<div class="bot-bubble">', unsafe_allow_html=True)
        st.markdown(solution)
        st.markdown('</div>', unsafe_allow_html=True)

        # Save to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": solution})
        st.session_state.solution_shown = True

        # ── Follow-up / Reset options ──────────────────────────
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Issue", key="btn_reset"):
                st.session_state.step = 1
                st.session_state.error_desc = ""
                st.session_state.selected_asset = None
                st.session_state.chat_history = []
                st.session_state.solution_shown = False
                st.rerun()
        with col2:
            if st.button("📋 Ask Follow-up", key="btn_followup"):
                st.session_state.step = 4
                st.rerun()

    elif st.session_state.step == 3 and st.session_state.solution_shown:
        # Already shown, just show buttons
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Issue", key="btn_reset2"):
                st.session_state.step = 1
                st.session_state.error_desc = ""
                st.session_state.selected_asset = None
                st.session_state.chat_history = []
                st.session_state.solution_shown = False
                st.rerun()
        with col2:
            if st.button("📋 Ask Follow-up", key="btn_followup2"):
                st.session_state.step = 4
                st.rerun()

    # ──────────────────────────────────────────────────────────
    # STEP 4 — Follow-up questions (free form chat)
    # ──────────────────────────────────────────────────────────
    elif st.session_state.step == 4:
        follow_up = st.text_input("Ask a follow-up question:", placeholder="e.g. How do I update the BIOS on this model?")
        if follow_up and st.button("Send", key="btn_send_followup"):
            with st.spinner("Thinking..."):
                combined = f"Original issue: {st.session_state.error_desc}\nFollow-up question: {follow_up}"
                response = get_ai_solution(combined, st.session_state.selected_asset)
            st.session_state.chat_history.append({"role": "user",     "content": follow_up})
            st.session_state.chat_history.append({"role": "assistant","content": response})
            st.rerun()

        if st.button("🔄 Start New Issue", key="btn_new"):
            st.session_state.step = 1
            st.session_state.error_desc = ""
            st.session_state.selected_asset = None
            st.session_state.chat_history = []
            st.session_state.solution_shown = False
            st.rerun()


# ─────────────────────────────────────────────
# PAGE 2 — MAINTENANCE DASHBOARD
# ─────────────────────────────────────────────
elif "🔔 Maintenance Dashboard" in page:

    st.markdown("# 🔔 Maintenance Dashboard")
    st.markdown("*Real-time view of all NTPC IT assets and their maintenance status*")

    # ── Show popup alerts at the top ──────────────────────────
    show_critical_alerts()

    st.markdown("---")

    # ── Summary Metric Cards ───────────────────────────────────
    overdue_count   = len(df[df["days_remaining"] < 0])
    thisweek_count  = len(df[(df["days_remaining"] >= 0) & (df["days_remaining"] <= 7)])
    thismonth_count = len(df[(df["days_remaining"] > 7)  & (df["days_remaining"] <= 30)])
    ok_count        = len(df[df["days_remaining"] > 30])

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
<div class="metric-box">
<div class="metric-num" style="color:#f85149">{overdue_count}</div>
<div class="metric-label">OVERDUE</div>
</div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
<div class="metric-box">
<div class="metric-num" style="color:#e3a414">{thisweek_count}</div>
<div class="metric-label">DUE THIS WEEK</div>
</div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
<div class="metric-box">
<div class="metric-num" style="color:#388bfd">{thismonth_count}</div>
<div class="metric-label">DUE THIS MONTH</div>
</div>""", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
<div class="metric-box">
<div class="metric-num" style="color:#3fb950">{ok_count}</div>
<div class="metric-label">ALL GOOD</div>
</div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Filters ───────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filter_status = st.selectbox("Filter by Status:",
            ["All", "🔴 OVERDUE", "🔴 DUE THIS WEEK", "🟠 DUE THIS MONTH", "🟡 UPCOMING", "🟢 OK"])
    with col_f2:
        filter_type = st.selectbox("Filter by Device Type:",
            ["All"] + sorted(df["device_type"].unique().tolist()))
    with col_f3:
        filter_crit = st.selectbox("Filter by Criticality:",
            ["All", "Critical", "High", "Medium", "Low"])

    # Apply filters
    filtered = df.copy()
    if filter_status != "All":
        filtered = filtered[filtered["status"] == filter_status]
    if filter_type != "All":
        filtered = filtered[filtered["device_type"] == filter_type]
    if filter_crit != "All":
        filtered = filtered[filtered["criticality"] == filter_crit]

    st.markdown(f"**Showing {len(filtered)} assets** (sorted by urgency)")

    # ── Asset table with color-coded rows ─────────────────────
    for _, row in filtered.iterrows():
        days = row["days_remaining"]
        days_str = f"{int(days)} days" if pd.notna(days) else "Unknown"

        # Pick card style based on status
        if pd.notna(days) and days < 0:
            card_class = "alert-critical"
        elif pd.notna(days) and days <= 7:
            card_class = "alert-high"
        elif pd.notna(days) and days <= 30:
            card_class = "alert-medium"
        else:
            card_class = "alert-ok"

        next_date = row["next_maintenance"].strftime("%d %b %Y") if pd.notna(row["next_maintenance"]) else "N/A"

        st.markdown(f"""
<div class="{card_class}">
<strong>{row['status']} &nbsp;|&nbsp; {row['asset_id']}</strong> — {row['device_type']} &nbsp;
<span style="color:#8b949e;font-size:0.85rem">{row['asset_make']} {row['model']}</span><br>
<small>
Next maintenance: <strong>{next_date}</strong> &nbsp;|&nbsp;
Days remaining: <strong>{days_str}</strong> &nbsp;|&nbsp;
Criticality: <strong>{row['criticality']}</strong> &nbsp;|&nbsp;
Urgency Score: <strong>{row['urgency_score']:.1f}</strong>
</small>
</div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Full Data Table (expandable) ──────────────────────────
    with st.expander("📊 View Full Asset Table"):
        display_cols = ["asset_id", "device_type", "asset_make", "model",
                        "criticality", "last_maintenance", "next_maintenance",
                        "days_remaining", "status", "urgency_score"]
        st.dataframe(
            filtered[display_cols].rename(columns={
                "asset_id": "ID", "device_type": "Type", "asset_make": "Brand",
                "model": "Model", "criticality": "Criticality",
                "last_maintenance": "Last Maintained", "next_maintenance": "Next Due",
                "days_remaining": "Days Left", "status": "Status",
                "urgency_score": "Urgency Score"
            }),
            use_container_width=True,
            height=400
        )
