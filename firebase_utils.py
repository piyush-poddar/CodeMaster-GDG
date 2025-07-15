import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase Admin
def init_firebase():
    if not firebase_admin._apps:
        firebase_admin.initialize_app()

# Verify ID token passed from frontend
def verify_token_and_store_user(id_token: str):
    try:
        decoded = auth.verify_id_token(id_token)
        st.session_state["user_email"] = decoded.get("email")
        st.session_state["user_uid"] = decoded.get("uid")
        return True, decoded.get("email")
    except Exception as e:
        return False, str(e)
