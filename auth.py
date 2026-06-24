import streamlit as st
import streamlit_authenticator as stauth

def authenticate_user():
    # ---------------------------------------
    # Generate hashed passwords (NEW API)
    # ---------------------------------------
    hashed_passwords = stauth.Hasher().generate(
        ["admin123", "analyst123"]
    )

    credentials = {
        "usernames": {
            "admin": {
                "name": "Admin User",
                "password": hashed_passwords[0],
                "role": "admin"
            },
            "analyst": {
                "name": "Fraud Analyst",
                "password": hashed_passwords[1],
                "role": "analyst"
            }
        }
    }

    authenticator = stauth.Authenticate(
        credentials,
        cookie_name="upi_fraud_cookie",
        key="upi_fraud_key",
        cookie_expiry_days=1
    )

    name, status, username = authenticator.login("Login", "main")

    if status is False:
        st.error("❌ Invalid username or password")
        st.stop()

    if status is None:
        st.warning("⚠ Please enter login credentials")
        st.stop()

    if status:
        role = credentials["usernames"][username]["role"]
        authenticator.logout("Logout", "sidebar")
        st.sidebar.success(f"Logged in as {name} ({role.upper()})")
        return role
