import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import numpy as np
import re

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(
    page_title="UPI Fraud Detection System",
    page_icon="💳",
    layout="wide"
)

# =================================================
# SIMPLE AUTH (SESSION-BASED, STABLE)
# =================================================
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "analyst": {"password": "analyst123", "role": "analyst"},
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.user = None

def login():
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.authenticated = True
            st.session_state.role = USERS[username]["role"]
            st.session_state.user = username
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

def logout():
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.user = None
    st.rerun()

if not st.session_state.authenticated:
    login()
    st.stop()

st.sidebar.success(
    f"Logged in as {st.session_state.user.upper()} "
    f"({st.session_state.role.upper()})"
)

if st.sidebar.button("Logout"):
    logout()

# =================================================
# UI STYLE
# =================================================
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0f172a; }
[data-testid="stSidebar"] { background-color: #020617; }
h1,h2,h3,h4,p,label { color: #e5e7eb !important; }
</style>
""", unsafe_allow_html=True)

st.title("💳 UPI Fraud Detection & Analysis")

# =================================================
# VALIDATION FUNCTIONS
# =================================================
def is_valid_upi(vpa):
    return re.match(r"^[a-zA-Z0-9]+@[a-zA-Z]+$", vpa) is not None

def is_valid_device(device):
    return re.match(r"^device_[0-9]+$", device) is not None

# =================================================
# 1️⃣ SINGLE TRANSACTION ANALYSIS (REAL-TIME MODE)
# =================================================
if st.session_state.role == "admin":
    st.subheader("🔍 Single Transaction Analysis (Real-Time)")

    c1, c2 = st.columns(2)

    with c1:
        txn_date = st.date_input("Transaction Date", datetime.date.today())
        txn_time = st.time_input("Transaction Time", datetime.datetime.now().time())
        amount = st.number_input("Transaction Amount (₹)", min_value=1.0, step=100.0)
        device_id = st.text_input("Device ID (e.g., device_66)")

    with c2:
        sender = st.text_input("Sender UPI ID (e.g., user12@paytm)")
        receiver = st.text_input("Receiver UPI ID (e.g., user9@ybl)")

    if st.button("Analyze Transaction"):
        errors = []
        risk_score = 0
        reasons = []

        # Normalize input
        sender = sender.strip().lower()
        receiver = receiver.strip().lower()
        device_id = device_id.strip().lower()

        # -------- FORMAT VALIDATION --------
        if not is_valid_upi(sender):
            errors.append("Invalid Sender UPI format")

        if not is_valid_upi(receiver):
            errors.append("Invalid Receiver UPI format")

        if not is_valid_device(device_id):
            errors.append("Invalid Device ID format")

        if errors:
            for e in errors:
                st.error(f"❌ {e}")
        else:
            # -------- RISK SCORING (NO DATASET) --------
            hour = txn_time.hour

            if amount > 100000:
                risk_score += 2
                reasons.append("Very high transaction amount")

            elif amount > 50000:
                risk_score += 1
                reasons.append("High transaction amount")

            if 0 <= hour <= 5:
                risk_score += 1
                reasons.append("Night-time transaction")

            if device_id.endswith(("0", "9")):
                risk_score += 1
                reasons.append("Unusual device pattern")

            # -------- FINAL DECISION --------
            if risk_score == 0:
                st.success("✅ TRANSACTION IS SAFE")
                st.write(f"Risk Score: {risk_score}")

            elif risk_score == 1:
                st.warning("⚠️ SUSPICIOUS TRANSACTION")
                st.write("Reason: Moderate risk detected")
                st.write(f"Risk Score: {risk_score}")
                for r in reasons:
                    st.write(f"- {r}")

            else:
                st.error("🚨 FRAUD DETECTED")
                st.write("Reason: High-risk transaction")
                st.write(f"Risk Score: {risk_score}")
                for r in reasons:
                    st.write(f"- {r}")

# =================================================
# 2️⃣ BATCH ANALYSIS (DATASET MODE)
# =================================================
st.markdown("---")
st.subheader("📊 Fraud Analysis Results (Dataset Based)")

uploaded = st.file_uploader(
    "Upload Fraud Dataset (CSV)",
    type=["csv"]
)

if uploaded is None:
    st.info("⬆ Upload dataset to view batch analysis")
    st.stop()

df = pd.read_csv(uploaded)

required_cols = [
    "amount", "vpa_sender", "vpa_receiver",
    "timestamp", "device_id", "is_fraud"
]

for col in required_cols:
    if col not in df.columns:
        st.error(f"Dataset must contain column: {col}")
        st.stop()

df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df["Date"] = df["timestamp"].dt.date
df["Hour"] = df["timestamp"].dt.hour

fraud_df = df[df["is_fraud"] == 1]

# =================================================
# METRICS
# =================================================
m1, m2, m3 = st.columns(3)
m1.metric("Total Transactions", len(df))
m2.metric("Fraud Transactions", len(fraud_df))
m3.metric("Fraud Rate (%)", f"{(len(fraud_df)/len(df))*100:.2f}")

# =================================================
# GRAPH 1 – PIE (FIRST)
# =================================================
st.subheader("📊 Fraud vs Safe Transactions")

fig1 = px.pie(
    df,
    names=df["is_fraud"].map({0: "Safe", 1: "Fraud"}),
    hole=0.5
)
fig1.update_traces(textinfo="percent+label")
st.plotly_chart(fig1, use_container_width=True)

# =================================================
# GRAPH 2 – DAY-WISE FRAUD COUNT
# =================================================
st.subheader("📊 Fraud Count – Day by Day")

daily = fraud_df.groupby("Date").size().reset_index(name="Fraud Count")
fig2 = px.line(daily, x="Date", y="Fraud Count", markers=True)
st.plotly_chart(fig2, use_container_width=True)

# =================================================
# GRAPH 3 – TOP FRAUD DEVICES
# =================================================
st.subheader("📊 Top Fraud Devices")

top_devices = fraud_df["device_id"].value_counts().head(10).reset_index()
top_devices.columns = ["Device ID", "Fraud Count"]
fig3 = px.bar(top_devices, x="Fraud Count", y="Device ID", orientation="h")
st.plotly_chart(fig3, use_container_width=True)

# =================================================
# ADMIN ONLY – DATA TABLE
# =================================================
if st.session_state.role == "admin":
    st.subheader("📄 Fraud Transactions Table (Admin Only)")
    st.dataframe(fraud_df, use_container_width=True)
