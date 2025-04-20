import streamlit as st
import requests
import json
import base64
import io
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import re
import time
import secrets

# Load environment variables
load_dotenv()

# API base URL
API_BASE_URL = "http://localhost:8000"

# Set page config
st.set_page_config(
    page_title="Email Management System",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #1c3956;
        color:#c7dceb;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #1c3956;
        color:#c7dceb;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .error-box {
        background-color: #FFEBEE;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None
if 'emails' not in st.session_state:
    st.session_state.emails = []
if 'last_activity' not in st.session_state:
    st.session_state.last_activity = datetime.now()
if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = 0
if 'last_login_attempt' not in st.session_state:
    st.session_state.last_login_attempt = datetime.now()
if 'login_blocked_until' not in st.session_state:
    st.session_state.login_blocked_until = None
if 'csrf_token' not in st.session_state:
    st.session_state.csrf_token = secrets.token_urlsafe(32)

# Validation functions
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_password(password):
    # Password must be at least 8 characters long
    if len(password) < 8:
        return False
    
    # Check for at least one uppercase letter
    if not any(c.isupper() for c in password):
        return False
    
    # Check for at least one lowercase letter
    if not any(c.islower() for c in password):
        return False
    
    # Check for at least one digit
    if not any(c.isdigit() for c in password):
        return False
    
    # Check for at least one special character
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False
    
    return True

def is_valid_username(name):
    # Username must be at least 2 characters long
    return len(name) >= 2

# Helper functions
def login(email, password, csrf_token):
    # Verify CSRF token
    if csrf_token != st.session_state.csrf_token:
        st.error("Invalid request. Please refresh the page and try again.")
        return False
    
    # Check if login is blocked
    if st.session_state.login_blocked_until and datetime.now() < st.session_state.login_blocked_until:
        remaining_time = (st.session_state.login_blocked_until - datetime.now()).seconds // 60
        st.error(f"Too many login attempts. Please try again in {remaining_time} minutes.")
        return False
    
    # Check rate limiting
    current_time = datetime.now()
    time_diff = current_time - st.session_state.last_login_attempt
    
    # Reset login attempts after 15 minutes
    if time_diff > timedelta(minutes=15):
        st.session_state.login_attempts = 0
    
    # Increment login attempts
    st.session_state.login_attempts += 1
    st.session_state.last_login_attempt = current_time
    
    # Block login after 5 failed attempts
    if st.session_state.login_attempts > 5:
        st.session_state.login_blocked_until = current_time + timedelta(minutes=15)
        st.error("Too many login attempts. Please try again in 15 minutes.")
        return False
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/token",
            data={"username": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["access_token"]
            # Reset login attempts on successful login
            st.session_state.login_attempts = 0
            # Generate new CSRF token after successful login
            st.session_state.csrf_token = secrets.token_urlsafe(32)
            return True
        else:
            st.error(f"Login failed: {response.json().get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return False

def register(name, email, password, confirm_password, csrf_token):
    # Verify CSRF token
    if csrf_token != st.session_state.csrf_token:
        st.error("Invalid request. Please refresh the page and try again.")
        return False
    
    # Validate all fields
    if not name or not email or not password or not confirm_password:
        st.error("Please enter all fields")
        return False
    
    # Validate email format
    if not is_valid_email(email):
        st.error("Please enter a valid email address")
        return False
    
    # Validate password
    if not is_valid_password(password):
        st.error("Password must be at least 8 characters long and contain uppercase, lowercase, number, and special character")
        return False
    
    # Validate username
    if not is_valid_username(name):
        st.error("Username must be at least 2 characters long")
        return False
    
    # Validate that passwords match
    if password != confirm_password:
        st.error("Passwords do not match")
        return False
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/users",
            json={"name": name, "email": email, "password": password}
        )
        if response.status_code == 200:
            # Generate new CSRF token after successful registration
            st.session_state.csrf_token = secrets.token_urlsafe(32)
            return True
        else:
            st.error(f"Registration failed: {response.json().get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return False

def fetch_emails():
    if not st.session_state.token:
        st.error("Please login first")
        return
    
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        # Get max_results from session state or default to 10
        max_results = st.session_state.get('max_results', 10)
        response = requests.get(f"{API_BASE_URL}/emails?max_results={max_results}", headers=headers)
        
        if response.status_code == 200:
            st.session_state.emails = response.json()
            return True
        else:
            st.error(f"Failed to fetch emails: {response.json().get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return False

def download_attachment(message_id, attachment_id):
    if not st.session_state.token:
        st.error("Please login first")
        return None
    
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.get(
            f"{API_BASE_URL}/emails/{message_id}/attachments/{attachment_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"Failed to download attachment: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

# Update last activity on any interaction
def update_last_activity():
    st.session_state.last_activity = datetime.now()

# Main app
def main():
    st.markdown("<h1 class='main-header'>Email Management System</h1>", unsafe_allow_html=True)
    
    # Update last activity
    update_last_activity()
    
    # Sidebar for authentication
    with st.sidebar:
        st.markdown("<h2 class='sub-header'>Authentication</h2>", unsafe_allow_html=True)
        
        if st.session_state.token:
            st.markdown("<div class='success-box'>You are logged in</div>", unsafe_allow_html=True)
            if st.button("Logout"):
                st.session_state.token = None
                st.session_state.user = None
                st.session_state.emails = []
                st.rerun()
        else:
            tab1, tab2 = st.tabs(["Login", "Register"])
            
            with tab1:
                st.markdown("<h3>Login</h3>", unsafe_allow_html=True)
                email = st.text_input("Email", key="login_email", placeholder="Please enter your email")
                password = st.text_input("Password", type="password", key="login_password", placeholder="Please enter your password")
                
                # Hidden CSRF token field
                csrf_token = st.session_state.csrf_token
                
                if st.button("Login"):
                    if login(email, password, csrf_token):
                        st.success("Login successful!")
                        update_last_activity()
                        st.rerun()
            
            with tab2:
                st.markdown("<h3>Register</h3>", unsafe_allow_html=True)
                name = st.text_input("Name", key="register_name", placeholder="Please enter your name")
                email = st.text_input("Email", key="register_email", placeholder="Please enter your email")
                password = st.text_input("Password", type="password", key="register_password", placeholder="Please enter your password")
                confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password", placeholder="Please confirm your password")
                
                # Hidden CSRF token field
                csrf_token = st.session_state.csrf_token
                
                if st.button("Register"):
                    if register(name, email, password, confirm_password, csrf_token):
                        st.success("Registration successful! Please login.")
    
    # Main content
    if st.session_state.token:
        # Email management section
        st.markdown("<h2 class='sub-header'>Email Listing</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("Fetch Emails"):
                with st.spinner("Fetching emails..."):
                    fetch_emails()
        
        with col2:
            max_results = st.number_input("Max Results", min_value=1, max_value=50, value=10, key="max_results_input")
            # Store the max_results value in session state
            st.session_state.max_results = max_results
        
        # Display emails
        if st.session_state.emails:
            st.markdown(f"<h3>Found {len(st.session_state.emails)} emails</h3>", unsafe_allow_html=True)
            
            # Convert emails to DataFrame for better display
            email_data = []
            for i, email in enumerate(st.session_state.emails):
                email_data.append({
                    "From": email.get("sender", "Unknown"),
                    "Subject": email.get("subject", "No Subject"),
                    "Date": email.get("timestamp", ""),
                    "Attachments": len(email.get("attachments", [])),
                })
            
            df = pd.DataFrame(email_data,index=range(1,len(email_data)+1))
            st.dataframe(df, use_container_width=True)
            
            # Email details and attachments
            st.markdown("<h3>Email Details</h3>", unsafe_allow_html=True)
            
            # Create a list of email subjects with index starting from 1
            email_options = [f"{i+1}. {email.get('subject', 'No Subject')}" for i, email in enumerate(st.session_state.emails)]
            
            selected_email_idx = st.selectbox(
                "Select an email to view details",
                range(len(st.session_state.emails)),
                format_func=lambda x: email_options[x]
            )
            
            if selected_email_idx is not None and selected_email_idx < len(st.session_state.emails):
                email = st.session_state.emails[selected_email_idx]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Subject:** {email.get('subject', 'No Subject')}")
                    st.write(f"**From:** {email.get('sender', 'Unknown')}")
                    st.write(f"**Date:** {email.get('timestamp', '')}")
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Display attachments
                if email.get("attachments"):
                    st.markdown("<h4>Attachments</h4>", unsafe_allow_html=True)
                    
                    for attachment in email.get("attachments", []):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Filename:** {attachment.get('filename', 'Unknown')}")
                            st.write(f"**Type:** {attachment.get('mimeType', 'Unknown')}")
                        
                        with col2:
                                attachment_data = download_attachment(
                                    email.get("message_id"),
                                    attachment.get("id")
                                )
                                
                                if attachment_data:
                                    # Create a download button
                                    st.download_button(
                                        label="Download File",
                                        data=attachment_data,
                                        file_name=attachment.get("filename", "attachment"),
                                        mime=attachment.get("mimeType", "application/octet-stream"),
                                        key=f"download_{attachment.get('id')}"
                                    )
        else:
            st.markdown("<div class='info-box' align='center'>No emails found. Click 'Fetch Emails' to load emails from your Gmail account.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='info-box' align='center'>Please login to access the email management system.</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main() 
