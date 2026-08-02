import streamlit as st
from utils import apply_global_styles, build_sidebar, create_user, authenticate_user, get_mongo_uri

# STEP 1: Restore the original, working page configuration
st.set_page_config(
    page_title="TaskFlow - Welcome",
    page_icon="✨",
    layout="wide"  # Use 'wide' layout to correctly center the form with columns
)

apply_global_styles()

if not get_mongo_uri():
    st.info("No MongoDB URI configured. The app is running in local demo mode using a JSON file.")

# --- PRIMARY LOGIC: REDIRECT OR SHOW LOGIN ---

# If the user is already logged in, immediately switch to the Home page.
if st.session_state.get("login_state"):
    st.switch_page("pages/1_🏠_Home.py")

# If not logged in, proceed to show the login page UI.

# Hide the sidebar on the login page
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

# Use columns to create the centered container for the login form
_ , login_col, _ = st.columns([1, 1, 1])

with login_col:
    # Your original, preferred login UI
    st.image("images/login_banner.png")
    st.markdown("<h1 style='text-align: center;'>🔐 TaskFlow Login</h1>", unsafe_allow_html=True)

    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    # Login Form
    with login_tab:
        with st.form("login_form"):
            login_username = st.text_input("Username", key="login_user")
            login_password = st.text_input("Password", type="password", key="login_pass")
            if st.form_submit_button("Login", use_container_width=True):
                user = authenticate_user(login_username, login_password)
                if user:
                    # On successful login, set the session state...
                    st.session_state["login_state"] = True
                    st.session_state["user"] = user["username"]
                    st.session_state["name"] = user["username"]
                    if 'tags' not in st.session_state: # Initialize tags on first login
                        st.session_state.tags = ["Work", "Personal", "Urgent", "Shopping"]
                    # ...and immediately switch to the Home page.
                    st.switch_page("pages/1_🏠_Home.py")
                else:
                    st.error("Invalid username or password.")

    # Signup Form
    with signup_tab:
        with st.form("signup_form"):
            signup_username = st.text_input("Choose a Username", key="signup_user")
            signup_password = st.text_input("Create a Password", type="password", key="signup_pass")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_pass_confirm")
            if st.form_submit_button("Sign Up", use_container_width=True):
                if signup_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    result = create_user(signup_username, signup_password)
                    if result is True:
                        st.success("Account created! You can now log in.")
                    else:
                        st.error(result)

# The script ends here for a non-logged-in user.
