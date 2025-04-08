import streamlit as st
from groq import Groq
import os
import sqlite3
import streamlit.components.v1 as components
from logger import AppLogger
from db_utils import get_connection, initialize_database
from ask_questions import run_ask_questions as run_chatbot_module
from load_data import run_upload_data
from hr_dashboard import run_dashboard
from answer_questions import run_quiz_module
from customise_questions_scenarios import run_assignments
from scenario_trainer import run_conversation_module
from add_scenario import run_generate_scenario_module


# Set environment variables
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["GROQ_API_KEY"] = "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"

# Initialize Groq client
client = Groq(api_key=os.environ["GROQ_API_KEY"])

# Connect to the SQLite database and initialize tables
conn = get_connection()
conn, cursor = initialize_database(conn)


# Page config
st.set_page_config(
        page_title="AIvolution | HR Onboarding Platform", 
        layout="wide",
        page_icon="aivolution_icon.png")
st.image("aivolution_logo.jpeg", width=280)

# Styling for aligned, uppercase, wide buttons
st.markdown("""
    <style>
    .sidebar-title {
        font-size: 18px !important;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    div.stButton > button {
        width: 100%;
        border: 1px solid #ccc;
        padding: 0.75rem 1rem;
        margin-bottom: 0.7rem;
        font-weight: 700;
        font-size: 15px;
        border-radius: 6px;
        text-align: center;
        background-color: #f0f2f6;
        color: #1c1c1c;
        text-transform: uppercase;
    }
    div.stButton > button:hover {
        background-color: #e4e9f2;
    }
    .active-tab > button {
        background-color: #0366d6 !important;
        color: white !important;
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# Init session state
if "page" not in st.session_state:
    st.session_state.page = "login"

# Function to handle user login with hardcoded users
def handle_login(username, password, role):
    # Connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Retrieve all user records
    cursor.execute("SELECT username, password, system_role FROM users")
    rows = cursor.fetchall()
    dummy_users = {username: {"password": password, "role": role} for username, password, role in rows}
    conn.close()

    if username in dummy_users:
        if dummy_users[username]["password"] == password and dummy_users[username]["role"] == role:
            st.session_state.user_role = dummy_users[username]["role"]
            st.session_state.username = username
            
            # Redirect based on role
            if role == "admin":
                st.session_state.page = "dashboard"
            elif role == "employee":
                st.session_state.page = "chat"

            st.success(f"Welcome {username}!")
            st.rerun()
        else:
            st.error("Role mismatch or incorrect password. Please try again.")
    else:
        st.error("Invalid username. Please try again.")

# Sidebar Navigation
def nav_button(label, page_key):
    if st.session_state.page == page_key:
        with st.sidebar.container():
            st.markdown('<div class="active-tab">', unsafe_allow_html=True)
            if st.button(label.upper(), key=page_key):
                st.session_state.page = page_key
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        if st.sidebar.button(label.upper(), key=page_key):
            st.session_state.page = page_key
            st.rerun()

# Render navigation buttons for pages
def render_navigation():
    if st.session_state.user_role == 'admin':
        nav_button("Upload Docs", "upload")
        nav_button("HR Dashboard", "dashboard")
        nav_button("Assign lessons", "assign")
        nav_button("Generate Scenarios", "generate")
    elif st.session_state.user_role == 'employee':
        nav_button("AI Assistant", "chat")
        nav_button("Take Quiz", "quiz")
        nav_button("Practice Scenario", "scenario")

# Main login page
def login_page():
    st.title("Select Your Role")

    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    role = st.selectbox("Select Role", ['admin', 'employee'])

    if st.button("Login"):
        handle_login(username, password, role)

# Function to handle user logout
def logout():
    del st.session_state["user_role"]
    del st.session_state["username"]
    del st.session_state["page"]
    st.session_state.page = "login"
    st.success("You have been logged out successfully.")
    st.rerun()

# Initialize logger
logger = AppLogger()

# Main content routing
if st.session_state.page == "login":
    login_page()

else:
    render_navigation()

    # Logout button
    if st.button("Logout"):
        logout()

    if st.session_state.page == "upload":
        run_upload_data(conn, cursor, client, logger)

    elif st.session_state.page == "chat":
        run_chatbot_module(client, logger)

    elif st.session_state.page == "quiz":
        run_quiz_module(conn, cursor, logger)

    elif st.session_state.page == "scenario":
        run_conversation_module(conn, cursor, logger)

    elif st.session_state.page == "dashboard":
        run_dashboard(logger)

    elif st.session_state.page == "assign":
        run_assignments(conn, cursor, client, logger)

    elif st.session_state.page == "generate":
        run_generate_scenario_module(conn, cursor)

# Footer
st.markdown("---")
st.caption("Built by Team AIvolution | NUS-GURU Network AI Innovation Challenge 2025")

# Embed ElevenLabs Conversational AI Widget
if "user_role" in st.session_state and st.session_state.user_role == "employee":
    components.html(
    """
    <elevenlabs-convai agent-id="WibiIDKxQ3zFxpbZ5A6z"></elevenlabs-convai>
    <script src="https://elevenlabs.io/convai-widget/index.js" async type="text/javascript"></script>
    """,
    height= 200  # You can adjust the height depending on your layout
)