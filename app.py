# Import the Streamlit library for building the UI.
import streamlit as st  # Streamlit primitives for UI.
# Import pandas to create a table-shaped data structure.
import pandas as pd  # DataFrame utilities for table data.
# Import date utilities to set today's date as the default.
from datetime import date, datetime  # Provides today's date and datetime checks.
# Import Supabase client factory for database access.
from supabase import create_client, ClientOptions  # Supabase client creation.
# Import time utilities for brief notice display.
import time  # Sleep for a short delay.
from contextlib import contextmanager  # Build Streamlit version-safe contexts.
# Import cookie manager for persistent auth sessions.
from streamlit_cookies_manager import CookieManager  # Cookie storage.
# Import auth handlers from the auth module.
from auth import auth  # Auth module with handlers.
#
# Normalize dates for consistent DataFrame serialization.
def normalize_date(value):  # Format date values as ISO strings.
    if isinstance(value, (date, datetime)):  # Convert date-like values.
        return value.isoformat()  # Use ISO string for consistency.
    return value  # Leave other values unchanged.


def render_dataframe(dataframe, height):  # Render a dataframe with version-safe args.
    safe_df = dataframe.copy()  # Avoid mutating caller.
    string_cols = safe_df.select_dtypes(include=["string", "object"]).columns  # Text columns.
    for col in string_cols:  # Coerce text columns to Python-backed strings.
        safe_df[col] = safe_df[col].astype("string[python]")  # Avoid Arrow LargeUtf8.
    try:  # Newer Streamlit supports hide_index.
        st.dataframe(
            safe_df,
            use_container_width=True,
            hide_index=True,
            height=height,
        )
    except TypeError:  # Older Streamlit rejects hide_index.
        st.dataframe(
            safe_df,
            use_container_width=True,
            height=height,
        )
#
# Provide a version-safe status context for older Streamlit releases.
@contextmanager
def status_context(message):  # Render a running status indicator when available.
    if hasattr(st, "status"):  # Streamlit 1.25+ supports status.
        with st.status(message, state="running") as status:  # Show status with spinner.
            yield status
    else:  # Fall back to spinner for Streamlit 1.19.
        with st.spinner(message):
            yield None


def safe_rerun():  # Rerun in a version-safe way.
    if hasattr(st, "rerun"):  # Streamlit 1.25+.
        st.rerun()
    else:  # Streamlit 1.19 fallback.
        st.experimental_rerun()
#
# Set the page title and icon in the browser tab.
st.set_page_config(page_title="Daily Workout Journal", page_icon="🏋️", layout="wide")  # Configure the page.
#
# Apply a simple, professional style to the UI.
st.markdown(  # Inject lightweight CSS for styling.
    """
<style>
:root {
  --bg-1: #f7f3ee;
  --bg-2: #f2f6f1;
  --ink-1: #1f2933;
  --ink-2: #52606d;
  --accent: #2f855a;
  --card: #ffffff;
  --border: #e4e7eb;
}
.stApp {
  background: radial-gradient(1200px 600px at 20% -10%, var(--bg-2), var(--bg-1));
  color: var(--ink-1);
}
/* Allow natural page scrolling on iOS (no fixed heights or overflow traps). */
html, body {
  height: auto !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  -webkit-overflow-scrolling: touch;
}
/* Prevent iOS scroll lock by allowing touch scroll on the app root. */
[data-testid="stAppViewContainer"] {
  overflow-y: auto !important;
  -webkit-overflow-scrolling: touch;
  touch-action: pan-y;
}
.block-container {
  padding-top: 0.1rem;
  padding-bottom: 0.2rem;
  padding-left: 1.1rem;
  padding-right: 1.1rem;
  max-width: 1200px;
  margin: 0 auto;
}
h1 {
  margin-bottom: 0.02rem;
}
.stCaption {
  margin-bottom: 0.1rem;
}
div[data-testid="stTextInput"],
div[data-testid="stNumberInput"],
div[data-testid="stSelectbox"],
div[data-testid="stDateInput"] {
  margin-bottom: 0.3rem;
}
label {
  margin-bottom: 0.12rem !important;
}
div[data-testid="stForm"] {
  gap: 0.2rem;
}
div.stButton {
  margin-top: 0.1rem;
}
[data-testid="stHeader"] {
  background: transparent;
}
div[data-testid="stVerticalBlock"] > div:has(.auth-card) {
  background: #f3f7f2;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 14px;
  box-shadow: 0 8px 24px rgba(16, 24, 40, 0.06);
}
.auth-card-wrap div[data-baseweb="tab-list"] {
  gap: 12px;
  border-bottom: 2px solid #e6e3de;
}
.auth-card-wrap button[role="tab"],
.auth-card-wrap [data-testid="stTabs"] button,
.auth-card-wrap [data-baseweb="tab"] {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 0 6px !important;
}
.auth-card-wrap button[role="tab"][aria-selected="true"],
.auth-card-wrap [data-testid="stTabs"] button[aria-selected="true"] {
  color: #e23c3c !important;
  border-bottom: 2px solid #e23c3c !important;
}
.auth-card-wrap [data-testid="stTabs"] div[role="tab"],
.auth-card-wrap [data-testid="stTabs"] button[role="tab"],
.auth-card-wrap [data-baseweb="tab"] {
  background: transparent !important;
  border-radius: 0 !important;
}
.auth-card-wrap [data-baseweb="tab"] > div,
.auth-card-wrap [data-baseweb="tab"] > div > p {
  background: transparent !important;
}
.auth-card-wrap div[data-baseweb="tab-list"] > button[data-baseweb="tab"] {
  background-color: transparent !important;
  border-color: transparent !important;
  box-shadow: none !important;
  outline: none !important;
}
.auth-card-wrap div[data-baseweb="tab-list"] > button[data-baseweb="tab"][aria-selected="false"] {
  background-color: transparent !important;
  border-color: transparent !important;
  box-shadow: none !important;
  outline: none !important;
}
.auth-card-wrap div[data-baseweb="tab-list"] > button[data-baseweb="tab"] * {
  background-color: transparent !important;
}
.auth-card-wrap div[data-baseweb="tab-list"] > button[data-baseweb="tab"][aria-selected="false"] * {
  background-color: transparent !important;
}
.auth-card-wrap .css-fg4pbf {
  background: transparent !important;
}
div[data-testid="stVerticalBlock"] > div:has(.auth-card) div[data-baseweb="tab-list"],
div[data-testid="stVerticalBlock"] > div:has(.auth-card) button[data-baseweb="tab"],
div[data-testid="stVerticalBlock"] > div:has(.auth-card) button[data-baseweb="tab"] * {
  background: transparent !important;
  box-shadow: none !important;
}
div[data-testid="stVerticalBlock"] > div:has(.auth-card) button[data-baseweb="tab"] {
  border: none !important;
  outline: none !important;
}
div[data-testid="stVerticalBlock"] > div:has(.auth-card) [data-baseweb="tab-highlight"] {
  background: #e23c3c !important;
}
.auth-card-wrap [data-baseweb="tab"]::before,
.auth-card-wrap [data-baseweb="tab"]::after {
  background: transparent !important;
  box-shadow: none !important;
}
.auth-card-wrap [data-baseweb="tab-highlight"] {
  background: #e23c3c !important;
}
.auth-card h3 {
  margin: 0;
  font-weight: 700;
  letter-spacing: 0.2px;
  color: var(--ink-1);
}
.auth-card h3::after {
  content: "";
  display: block;
  width: 64px;
  height: 3px;
  background: var(--accent);
  border-radius: 999px;
  margin-top: 6px;
}
.subtle-text {
  color: var(--ink-2);
}
button[kind="primary"] {
  background: linear-gradient(180deg, #7fcf9b, #62b984) !important;
  border: 1px solid #62b984 !important;
}
div.stButton > button[kind="primary"] {
  border-radius: 10px;
  padding: 0.4rem 1rem;
  font-weight: 600;
  border: 1px solid #62b984 !important;
  color: #ffffff;
  background: linear-gradient(180deg, #7fcf9b, #62b984) !important;
  white-space: nowrap;
}
button[aria-label="Finish Workout"] {
  background: linear-gradient(180deg, #7fcf9b, #62b984) !important;
  border-color: #62b984 !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}
div.stButton > button[aria-label="Finish Workout"]:not(:disabled) {
  background: linear-gradient(180deg, #7fcf9b, #62b984) !important;
  border-color: #62b984 !important;
  color: #ffffff !important;
  font-weight: 700 !important;
  box-shadow: 0 10px 20px rgba(98, 185, 132, 0.35);
  transform: translateY(-1px);
}
div[data-testid="stForm"] button[kind="primary"]:not([aria-label="Finish Workout"]),
div[data-testid="stFormSubmitButton"] > button:not([aria-label="Finish Workout"]),
button[aria-label="Add Workout"] {
  background: linear-gradient(180deg, #e3f6e9, #d3f0df) !important;
  background-color: #d3f0df !important;
  border-color: #c3e7d2 !important;
  color: #1f2933 !important;
}
div[data-testid="stFormSubmitButton"] > button[aria-label="Finish Workout"] {
  background: linear-gradient(180deg, #7fcf9b, #62b984) !important;
  border-color: #62b984 !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}
div.stButton > button[kind="secondary"] {
  margin-left: 0 !important;
  color: #1f2933 !important;
  background: #e6e9ef !important;
  border-color: #c7ccd6 !important;
}
div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button[kind="secondary"] {
  padding: 0.3rem 0.6rem !important;
  font-size: 0.85rem !important;
}
div.stButton > button[kind="primary"]:hover {
  filter: brightness(1.03);
}
div.stButton > button:disabled {
  color: #ffffff;
  opacity: 0.35;
  cursor: not-allowed;
  filter: blur(1.2px) grayscale(0.2) brightness(0.85);
  box-shadow: none !important;
}
div[data-testid="stFormSubmitButton"] > button:disabled {
  color: #ffffff !important;
  opacity: 0.35 !important;
  cursor: not-allowed !important;
  filter: blur(1.2px) grayscale(0.2) brightness(0.85) !important;
  box-shadow: none !important;
}
div[data-testid="stFormSubmitButton"] > button[aria-label="Finish Workout"]:disabled {
  opacity: 0.35 !important;
  filter: blur(1.2px) grayscale(0.2) brightness(0.85) !important;
  box-shadow: none !important;
}
div.stButton > button:not(:disabled) {
  filter: none;
  opacity: 1;
}
div[data-testid="stButton"]:has(button[aria-label="Workout History"]) {
  text-align: left;
  margin-right: auto;
}
div[data-testid="stExpander"] > details {
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--card);
}
div[data-testid="stExpander"] summary {
  font-weight: 600;
}
div[data-testid="stForm"] {
  gap: 0.4rem;
}
div[data-testid="stDataFrame"] {
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(16, 24, 40, 0.04);
  margin-left: auto;
  margin-right: auto;
  width: 100%;
}
.stDataFrame thead tr th {
  background: #f3f4f6;
  font-weight: 600;
}
.workout-toast {
  background: #e6f4ea;
  border: 1px solid #b7e1c1;
  color: #1f3d2b;
  padding: 10px 12px;
  border-radius: 10px;
  font-weight: 600;
}
div[data-testid="stVerticalBlock"] > div {
  padding-top: 0.1rem;
  padding-bottom: 0.1rem;
}
.auth-card-wrap {
  max-width: 420px;
  margin: 0 auto;
}
.auth-card-wrap .stTextInput,
.auth-card-wrap .stTextInput input {
  width: 100% !important;
}
@media (max-width: 768px) {
  .block-container {
    padding-left: 0.8rem;
    padding-right: 0.8rem;
    max-width: 100%;
  }
  div[data-testid="column"] {
    flex: 0 0 100% !important;
    width: 100% !important;
  }
  div[data-testid="stVerticalBlock"] > div {
    padding-top: 0.05rem;
    padding-bottom: 0.05rem;
  }
  .auth-card-wrap {
    max-width: 100%;
  }
}
input, textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {
  border: none !important;
  box-shadow: none !important;
}
.stTextInput div[data-baseweb="base-input"], .stTextInput div[data-baseweb="base-input"] > div,
/* Keep number inputs on default styling to avoid inner bracket artifacts. */
.stSelectbox div[data-baseweb="select"] > div {
  border: 1px solid #4a5568 !important;
  border-bottom: 1px solid #4a5568 !important;
  box-shadow: none !important;
  border-radius: 8px !important;
}
.stTextInput input, .stTextInput input[type="password"] {
  height: 2.5rem !important;
  min-height: 2.5rem !important;
  width: 100% !important;
  border-radius: 8px !important;
  box-sizing: border-box !important;
}
/* Keep selectboxes non-editable: hide caret and use pointer cursor. */
div[data-testid="stSelectbox"] input,
div[data-testid="stSelectbox"] [role="combobox"],
div[data-testid="stSelectbox"] div[data-baseweb="select"] input {
  caret-color: transparent !important;
  cursor: pointer !important;
  user-select: none !important;
}
div[data-testid="stSelectbox"],
div[data-testid="stSelectbox"] div[data-baseweb="select"] {
  cursor: pointer !important;
}
div[data-testid="stSelectbox"] * {
  caret-color: transparent !important;
}
</style>
""",
    unsafe_allow_html=True,
)
#
# =========================
# Header Layout (Rendered After Auth State)
# =========================
#
# Show any pending auth notice after a redirect.
if "auth_notice" in st.session_state:  # Check for stored notice.
    st.success(st.session_state.pop("auth_notice"))  # Show and clear notice.
    time.sleep(0.5)  # Keep the notice visible briefly.
    if hasattr(st, "rerun"):  # Use modern Streamlit API when available.
        safe_rerun()  # Rerun to remove the notice.
    else:  # Fallback for older versions.
        st.experimental_rerun()  # Rerun to remove the notice.
#
# Read Supabase credentials from Streamlit secrets.
supabase_url = st.secrets.get("SUPABASE_URL", "")  # Supabase URL.
# Read Supabase key from Streamlit secrets.
supabase_key = st.secrets.get("SUPABASE_KEY", "")  # Supabase anon key.
# Initialize cookie manager for persistent sessions.
cookie_manager = CookieManager()  # Create cookie manager.
# Ensure cookies are ready before continuing.
cookies_ready = cookie_manager.ready()  # Check cookie readiness.
if not cookies_ready:  # Warn when cookies are not ready.
    st.warning("Cookies not ready; running without persistence.")  # Show status message.
# Track cookie saves to avoid duplicate component keys.
if "pending_cookie_save" not in st.session_state:  # Initialize save flag.
    st.session_state["pending_cookie_save"] = False  # Default to no save.
# Reset per-run cookie save guard.
st.session_state["cookie_save_ran"] = False  # Allow one save per run.

# Queue a cookie save to run once per script.
def queue_cookie_save():  # Schedule cookie persistence.
    if cookies_ready:  # Only queue when cookies are ready.
        st.session_state["pending_cookie_save"] = True  # Mark save needed.
# Create the Supabase client when credentials are present.
supabase = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None  # Client.
# Provide the Supabase client to the auth module.
auth.supabase = supabase  # Share client with auth handlers.
# Provide the cookie manager to the auth module.
auth.cookies = cookie_manager  # Share cookies with auth handlers.
# Provide the auth API URL to the auth module.
auth.auth_api_url = st.secrets.get("AUTH_API_URL", "http://localhost:8000")  # Auth API base URL.
#
# Process any auth callback in the URL before rendering the UI.
auth.handle_auth_callback()  # Handle email confirmation or session callbacks.
#
# Restore a session from stored tokens when available.
auth.restore_session()  # Restore session after refreshes.
#
# Initialize the user session state if missing.
if "user" not in st.session_state:  # Check for user key.
    st.session_state["user"] = None  # Default to no user.
#
# Define the logout handler.
def handle_logout():  # Handle logout requests.
    auth.handle_logout()  # Delegate to auth module.
#
# Render the account expander for logged-in users.
def render_account_expander():  # Draw the account UI.
    if st.session_state.get("welcome_shown") is False:  # Show welcome once per login.
        st.success("Welcome back!")  # Welcome message.
        st.session_state["welcome_shown"] = True  # Mark welcome as shown.
        time.sleep(1)  # Keep the message visible briefly.
        if hasattr(st, "rerun"):  # Use modern Streamlit API when available.
            safe_rerun()  # Rerun to remove the message.
        else:  # Fallback for older versions.
            st.experimental_rerun()  # Rerun to remove the message.
    user_obj = st.session_state.get("user")  # Read user object.
    user_email = st.session_state.get("user_email", "")  # Read stored email.
    user_name = st.session_state.get("user_name", "")  # Read stored name.
    if user_obj is not None and not user_email:  # Extract from user if missing.
        user_email = getattr(user_obj, "email", "")  # Read attribute email.
        if not user_email and isinstance(user_obj, dict):  # Handle dict users.
            user_email = user_obj.get("email", "")  # Read dict email.
    display_name = user_name or user_email  # Prefer name, fall back to email.
    with st.expander(display_name or "Account"):  # Expand to show details.
        if user_email:  # Show email if available.
            st.write(user_email)  # Display full email.
        if st.button("Logout", type="primary"):  # Render logout button.
            handle_logout()  # Execute logout.

# Render the login/signup UI.
def render_login_signup_ui():  # Draw the auth UI.
    # Compact auth card with tabs for login/signup.
    st.markdown('<div class="auth-card"><h3>Your Account</h3></div>', unsafe_allow_html=True)  # Section header.
    # Center the auth card on desktop and keep it full width on mobile.
    auth_left, auth_center, auth_right = st.columns([1, 1.2, 1], gap="small")  # Centered card.
    with auth_center:  # Centered auth form column.
        st.markdown("<div class='auth-card-wrap'>", unsafe_allow_html=True)  # Auth card wrapper.
        tabs = st.tabs(["Login", "Sign up"])  # Tabbed auth UI.
        with tabs[0]:  # Login tab.
            email = st.text_input("Email", key="auth_email_login", placeholder="you@example.com")  # Email input field.
            password = st.text_input(  # Password input field.
                "Password",  # Label.
                type="password",  # Hide input.
                key="auth_password_login",  # Session key.
                placeholder="Enter your password",  # Placeholder text.
            )
            if st.button("Login", type="primary"):  # Render login button.
                if not email or "@" not in email:  # Basic email validation.
                    st.error("Enter a valid email address.")  # Prompt for valid email.
                elif not password:  # Guard empty password.
                    st.error("Enter your password.")  # Prompt for password.
                else:
                    auth.handle_login(email, password)  # Execute login.
        with tabs[1]:  # Signup tab.
            name = st.text_input("Name", key="auth_name_signup", placeholder="Your name")  # Name input field.
            email = st.text_input("Email", key="auth_email_signup", placeholder="you@example.com")  # Email input field.
            password = st.text_input(  # Password input field.
                "Password",  # Label.
                type="password",  # Hide input.
                key="auth_password_signup",  # Session key.
                placeholder="Create a password",  # Placeholder text.
            )
            if st.button("Sign Up", type="primary"):  # Render signup button.
                if not email or "@" not in email:  # Basic email validation.
                    st.error("Enter a valid email address.")  # Prompt for valid email.
                elif not password:  # Guard empty password.
                    st.error("Create a password.")  # Prompt for password.
                else:
                    auth.handle_signup(email, password, name)  # Execute signup.
        st.markdown("</div>", unsafe_allow_html=True)  # Close auth card wrapper.
#
# =========================
# Authentication UI Section
# =========================
# Show the authentication UI at the top of the page when logged out.
is_logged_in = st.session_state.get("user") or st.session_state.get("user_email")  # Logged-in flag.

# =========================
# Header Layout (Top-Aligned)
# =========================
header_container = st.container()  # Stable header container.
with header_container:  # Header content block.
    header_left, header_right = st.columns([3.1, 1], gap="small")  # Split header area.
    with header_left:  # Left side header.
        st.title("Daily Workout Journal")  # Title for the UI.
        st.caption("Log your session on the left and review your entries on the right.")  # Helper text.
    with header_right:  # Right side header.
        if is_logged_in:  # Show account controls on the top-right.
            render_account_expander()  # Render account expander.
            st.markdown("<div id='workout-history-btn'>", unsafe_allow_html=True)  # History button wrapper.
            if st.button("Workout History", key="workout_history", type="secondary"):  # Show history button.
                history_data = auth.fetch_history()  # Fetch workout history.
                if history_data:  # Store when data is returned.
                    st.session_state["history_data"] = history_data  # Persist history payload.
                    st.session_state["show_history"] = True  # Toggle history panel on.
            st.markdown("</div>", unsafe_allow_html=True)  # Close wrapper.
        else:  # Keep header spacing stable.
            st.markdown("&nbsp;")  # Spacer for layout stability.

# Render login/signup UI after header when logged out.
if not is_logged_in:  # Only render login UI when logged out.
    render_login_signup_ui()  # Render auth controls.
#
# Stop the app when the user is not logged in.
if not (st.session_state.get("user") or st.session_state.get("user_email")):  # Guard the workout form.
    st.info("Please log in to add workouts.")  # Prompt for login.
    st.stop()  # Prevent the rest of the UI from rendering.
#
# Show a workout completion notice if available.
workout_notice = st.session_state.pop("workout_notice", None)  # Read and clear notice.
if workout_notice:  # Check for workout notice.
    st.markdown(  # Render a styled success banner.
        f"<div class='workout-toast'>{workout_notice}</div>",
        unsafe_allow_html=True,
    )
# Show workout history panel when requested.
if st.session_state.get("show_history") and st.session_state.get("history_data"):  # Render history panel.
    history_data = st.session_state["history_data"]  # Read history payload.
    with st.expander("Workout History Summary", expanded=True):  # History summary panel.
        current_period = st.session_state.get("history_period", "All time")  # Read current period.
        period_label = st.selectbox(  # Period filter selector.
            "Period",  # Label.
            ["All time", "Week", "Month", "Year"],  # Period options.
            key="history_period",  # Session key.
        )
        if st.session_state.get("history_period_last") != period_label:  # Fetch when selection changes.
            st.session_state["history_period_last"] = period_label  # Track latest selection.
            period_value = None if period_label == "All time" else period_label.lower()  # Map to API value.
            history_data = auth.fetch_history(period=period_value)  # Fetch history payload.
            if history_data:  # Update stored history data.
                st.session_state["history_data"] = history_data  # Persist updated history.
        history_data = st.session_state.get("history_data", history_data)  # Refresh local data.
        metric_col1, metric_col2 = st.columns(2, gap="small")  # Metric row.
        metric_col1.metric("Total Sessions", history_data.get("total_sessions", 0))  # Sessions count.
        metric_col2.metric("Total Days", history_data.get("total_days", 0))  # Days count.
        if st.session_state.get("debug_history"):  # Optional debug panel.
            st.json(history_data)  # Show raw history payload.
        sessions_by_day = history_data.get("sessions_by_day", [])  # Read per-day data.
        if sessions_by_day:  # Show the table when data exists.
            history_table = pd.DataFrame(  # Build the display table.
                [{"Date": row.get("date"), "Session": row.get("count")} for row in sessions_by_day]
            )
            history_height = 36 + min(len(history_table), 10) * 35  # Fit height to rows.
            render_dataframe(history_table, history_height)  # Render the table.
# Remember completion state across refreshes.
if "workout_completed" not in st.session_state:  # Initialize completion flag.
    if cookies_ready:  # Load from cookie when available.
        st.session_state["workout_completed"] = cookie_manager.get("workout_completed") == "true"  # Load from cookie.
    else:  # Fall back when cookies are unavailable.
        st.session_state["workout_completed"] = False  # Default to not completed.
if workout_notice:  # Mark workout as completed when notice is shown.
    st.session_state["workout_completed"] = True  # Persist completion state.
    if cookies_ready:  # Persist in cookie when available.
        cookie_manager["workout_completed"] = "true"  # Persist in cookie.
        queue_cookie_save()  # Commit cookie changes once.
show_form = (  # Determine whether to show the entry form.
    not st.session_state["workout_completed"]  # Hide the form after completion.
    and not st.session_state.get("show_history")  # Hide the form when history is open.
)
#
# Restore the latest workout summary after refresh when completed.
if st.session_state["workout_completed"] and not st.session_state.get("workout_rows"):  # Restore summary.
    if supabase is not None:  # Only fetch when configured.
        access_token = auth.ensure_access_token()  # Read or refresh access token.
        last_session_id = st.session_state.get("last_session_id")  # Session id from state.
        if cookies_ready and not last_session_id:  # Fallback to cookie.
            last_session_id = cookie_manager.get("last_session_id")  # Session id from cookie.
        user_id = None  # Default user id.
        if st.session_state.get("user"):  # Read user id from session user.
            user_id = getattr(st.session_state["user"], "id", None)  # Read attribute id.
        if user_id is None and isinstance(st.session_state.get("user"), dict):  # Read dict user id.
            user_id = st.session_state["user"].get("id")  # Read dict id.
        if access_token and user_id and last_session_id:  # Only fetch when authenticated.
            authed_supabase = create_client(  # Create a new client with an auth header.
                supabase_url,  # Supabase URL.
                supabase_key,  # Supabase anon key.
                options=ClientOptions(headers={"Authorization": f"Bearer {access_token}"}),  # Auth header.
            )
            try:  # Attempt to set PostgREST auth header.
                authed_supabase.postgrest.auth(access_token)  # Apply auth token.
            except Exception:  # Ignore if not supported by client.
                pass  # Continue with fetch.
            session_lookup = authed_supabase.table("workout_sessions").select(  # Fetch session by id.
                "id,date,daytype"
            ).eq(  # Filter by session id.
                "id", last_session_id
            ).eq(  # Filter by user id.
                "user_id", user_id
            ).limit(1).execute()  # Execute query.
            if session_lookup.data:  # Proceed when a session exists.
                session = session_lookup.data[0]  # Read the session row.
                entries = authed_supabase.table("workout_entries").select(  # Fetch entries.
                    "exercise_name,weight,rep"
                ).eq(  # Filter by session id.
                    "session_id", session.get("id")
                ).execute()  # Execute query.
                restored_rows = []  # Build restored table rows.
                for entry in entries.data or []:  # Iterate through entry rows.
                    restored_rows.append(  # Add a row for display.
                        {
                            "Date": normalize_date(session.get("date")),  # Session date.
                            "Daytype ▼": session.get("daytype"),  # Session day type.
                            "Exercise Name": entry.get("exercise_name"),  # Exercise name.
                            "Weight (kg)": entry.get("weight"),  # Weight value.
                            "Rep": entry.get("rep"),  # Rep value.
                        }
                    )
                st.session_state["workout_rows"] = restored_rows  # Restore summary rows.
#
# Define the mapping from day type to exercise options.
# Define the mapping from day type to exercise options.
daytype_to_exercises = {  # Map day types to allowed exercises.
    "arm": [  # Arm day options.
        "prechair arm curl",  # Biceps curl variant.
        "tricep overhead press",  # Tricep movement.
        "tricep extension",  # Tricep movement.
        "Hammer curl",  # Biceps curl variant.
    ],  # End arm options.
    "leg": [  # Leg day options.
        "calf press",  # Calf exercise.
        "leg curl",  # Hamstring exercise.
        "squat",  # Compound leg movement.
        "leg extension",  # Quad isolation.
    ],  # End leg options.
    "push": [  # Push day options.
        "tricep overhead press",  # Tricep movement.
        "tricep extension",  # Tricep movement.
        "should press",  # Shoulder press.
        "lateral cable raise",  # Side delts.
        "rear delt",  # Rear delts.
        "chest press",  # Chest movement.
    ],  # End push options.
    "pull": [  # Pull day options.
        "prechair arm curl",  # Biceps curl variant.
        "Hammer curl",  # Biceps curl variant.
        "vertical back",  # Vertical pulling.
        "horizontal back",  # Horizontal pulling.
        "shruggs",  # Traps exercise.
    ],  # End pull options.
}  # End mapping.
#
# Define the default day type.
default_daytype = "push"  # Default to push day.
# Define the default exercise list for the default day type.
default_exercises = daytype_to_exercises[default_daytype]  # Default exercise list.
#
# Constants for custom options.
PREDEFINED_DAYTYPES = ["push", "pull", "leg", "arm"]  # Built-in day types.
ADD_DAYTYPE_OPTION = "➕ Add custom day type"  # Add day type trigger.
ADD_EXERCISE_OPTION = "➕ Add custom exercise"  # Add exercise trigger.
#
# Normalize text for case-insensitive uniqueness.
def normalize_label(value):  # Normalize day types and exercise names.
    return value.strip().lower()  # Trim and lowercase input.
#
# Build the list of day type options for the selector.
def build_daytype_options(custom_daytypes):  # Merge built-in and custom day types.
    options = []  # Ordered options list.
    seen = set()  # Track normalized names.
    for name in PREDEFINED_DAYTYPES + custom_daytypes:  # Combine predefined + custom.
        key = normalize_label(name)  # Normalize for comparison.
        if key in seen:  # Skip duplicates.
            continue
        options.append(name)  # Preserve display casing.
        seen.add(key)  # Track normalized key.
    return options  # Return unique options.
#
# Build the list of exercises for a day type.
def build_exercise_options(daytype_key, custom_exercises):  # Merge built-in and custom exercises.
    base_exercises = daytype_to_exercises.get(daytype_key, [])  # Built-in list for this day type.
    extras = custom_exercises.get(daytype_key, [])  # Custom list for this day type.
    options = []  # Ordered options list.
    seen = set()  # Track normalized names.
    for name in base_exercises + extras:  # Combine built-in + custom.
        key = normalize_label(name)  # Normalize for comparison.
        if key in seen:  # Skip duplicates.
            continue
        options.append(name)  # Preserve display casing.
        seen.add(key)  # Track normalized key.
    return options  # Return unique options.
#
# Initialize the table storage in session state if missing.
if "workout_rows" not in st.session_state:  # Check for stored rows.
    st.session_state["workout_rows"] = []  # Start with an empty list.
#
# Initialize the active day session in session state if missing.
if "active_daytype" not in st.session_state:  # Check for active day type.
    st.session_state["active_daytype"] = None  # Start with no active day type.
# Initialize the active date session in session state if missing.
if "active_date" not in st.session_state:  # Check for active date.
    st.session_state["active_date"] = None  # Start with no active date.
# Initialize the active session id in session state if missing.
if "active_session_id" not in st.session_state:  # Check for active session id.
    st.session_state["active_session_id"] = None  # Start with no active session id.
#
# Initialize custom day type/exercise storage in session state.
if "custom_daytypes" not in st.session_state:  # Track custom day types.
    st.session_state["custom_daytypes"] = []  # Start with no custom day types.
if "custom_daytypes_loaded" not in st.session_state:  # Track fetch status.
    st.session_state["custom_daytypes_loaded"] = False  # Default to not loaded.
if "custom_exercises" not in st.session_state:  # Track custom exercises per day type.
    st.session_state["custom_exercises"] = {}  # Map daytype_key -> exercises.
if "custom_exercises_loaded" not in st.session_state:  # Track per-daytype fetch status.
    st.session_state["custom_exercises_loaded"] = set()  # Default to empty set.
if "last_daytype_selection" not in st.session_state:  # Track day type changes.
    st.session_state["last_daytype_selection"] = None  # Default to no selection.
if "pending_daytype_selection" not in st.session_state:  # Defer day type selection updates.
    st.session_state["pending_daytype_selection"] = None  # Default to none.
if "pending_daytype_input_clear" not in st.session_state:  # Defer clearing day type input.
    st.session_state["pending_daytype_input_clear"] = False  # Default to no clear.
if "pending_exercise_selection" not in st.session_state:  # Defer exercise selection updates.
    st.session_state["pending_exercise_selection"] = None  # Default to none.
if "pending_exercise_input_clear" not in st.session_state:  # Defer clearing exercise input.
    st.session_state["pending_exercise_input_clear"] = False  # Default to no clear.
if "add_workout_clicked" not in st.session_state:  # Track Add Workout clicks across reruns.
    st.session_state["add_workout_clicked"] = False  # Default to not clicked.
if "finish_workout_clicked" not in st.session_state:  # Track Finish Workout clicks across reruns.
    st.session_state["finish_workout_clicked"] = False  # Default to not clicked.
if "done_clicked" not in st.session_state:  # Track Done button clicks across reruns.
    st.session_state["done_clicked"] = False  # Default to not clicked.
if "entry_weight" not in st.session_state:  # Initialize weight input state.
    st.session_state["entry_weight"] = 0.0  # Default weight.
if "entry_rep" not in st.session_state:  # Initialize rep input state.
    st.session_state["entry_rep"] = 0  # Default reps.
#
# Read the active session values for the current run.
active_daytype = st.session_state["active_daytype"]  # Current active day type.
# Read the active session date for the current run.
active_date = st.session_state["active_date"]  # Current active date.
# Read the active session id for the current run.
active_session_id = st.session_state["active_session_id"]  # Current active session id.
# Determine whether the user is in an active day session.
is_active_session = (  # Active flag.
    active_daytype is not None and active_date is not None
)
#
# Reset custom option caches when the authenticated user changes.
# NOTE: This prevents cross-user leakage when the same browser session logs in as different users.
current_user_id = None  # Default user id.
if st.session_state.get("user"):  # Read user id from session user.
    current_user_id = getattr(st.session_state["user"], "id", None)  # Read attribute id.
if current_user_id is None and isinstance(st.session_state.get("user"), dict):  # Read dict user id.
    current_user_id = st.session_state["user"].get("id")  # Read dict id.
if st.session_state.get("custom_user_id") != current_user_id:  # Clear caches on user change.
    st.session_state["custom_user_id"] = current_user_id  # Track current user id.
    st.session_state["custom_daytypes"] = []  # Reset day types.
    st.session_state["custom_daytypes_loaded"] = False  # Force reload.
    st.session_state["custom_exercises"] = {}  # Reset exercises.
    st.session_state["custom_exercises_loaded"] = set()  # Reset loaded flags.
    st.session_state["last_daytype_selection"] = None  # Reset day type selection.
    st.session_state["pending_daytype_selection"] = None  # Clear pending day type.
    st.session_state["pending_daytype_input_clear"] = False  # Clear pending day type input.
    st.session_state["pending_exercise_selection"] = None  # Clear pending exercise.
    st.session_state["pending_exercise_input_clear"] = False  # Clear pending exercise input.
#
# Load custom day types once per session for authenticated users.
if not st.session_state.get("custom_daytypes_loaded"):  # Fetch once per session.
    custom_daytypes = auth.fetch_custom_daytypes()  # Load from API.
    st.session_state["custom_daytypes"] = custom_daytypes  # Store day types.
    st.session_state["custom_daytypes_loaded"] = True  # Mark as loaded.
#
# =========================
# Main Two-Column Layout
# =========================
main_container = st.container()  # Stable main content block.
with main_container:  # Scope the main layout.
    left_col, right_col = st.columns([1.05, 1.95], gap="small")  # Two-column layout.
submitted = False  # Default submit state when form is hidden.
#
# Build the input form in the left column.
with left_col:  # Scope the form to the left column.
    if not show_form:  # Hide entry form after completion.
        st.markdown("&nbsp;")  # Keep layout spacing consistent.
    else:  # Render the entry form.
    # Keep the day type selector outside the form so it updates exercise options immediately.
        top_row_left, top_row_right = st.columns([1, 1], gap="small")  # Top row layout.
        with top_row_left:  # Daytype column.
            custom_daytypes = st.session_state.get("custom_daytypes", [])  # Read custom day types.
            daytype_options = build_daytype_options(custom_daytypes)  # Merge day type options.
            daytype_options_with_add = daytype_options + [ADD_DAYTYPE_OPTION]  # Add custom trigger.
            pending_daytype = st.session_state.get("pending_daytype_selection")  # Pending selection.
            if pending_daytype:  # Apply pending selection before widget renders.
                st.session_state["entry_daytype"] = pending_daytype  # Update selection safely.
                st.session_state["pending_daytype_selection"] = None  # Clear pending.
            if st.session_state.get("pending_daytype_input_clear"):  # Clear input before widget.
                st.session_state["custom_daytype_input"] = ""  # Clear input safely.
                st.session_state["pending_daytype_input_clear"] = False  # Reset flag.
            selected_daytype = active_daytype if is_active_session else st.session_state.get("entry_daytype")  # Current.
            daytype_index = 0  # Default index.
            if "entry_daytype" not in st.session_state:  # Only set index when no session value exists.
                try:  # Resolve the default index.
                    daytype_index = daytype_options_with_add.index(selected_daytype)  # Match stored selection.
                except ValueError:  # Fall back to the first option.
                    daytype_index = 0  # Default index.
            entry_daytype = st.selectbox(  # Day type selector.
                "Daytype ▼",  # Label.
                options=daytype_options_with_add,  # Allowed day types + custom.
                index=daytype_index,  # Active or default.
                disabled=is_active_session,  # Lock selection during active session.
                key="entry_daytype",  # Session key for reset support.
            )  # End day type selectbox.
            if entry_daytype == ADD_DAYTYPE_OPTION and not is_active_session:  # Show custom input.
                custom_daytype_input = st.text_input(  # Custom day type input.
                    "Custom day type",  # Label.
                    key="custom_daytype_input",  # Session key.
                    placeholder="e.g. conditioning",  # Placeholder text.
                )
                save_daytype_clicked = st.button(  # Save custom day type.
                    "Save day type",  # Button label.
                    type="secondary",  # Secondary styling.
                )
                if save_daytype_clicked:  # Persist custom day type.
                    result = auth.add_custom_daytype(custom_daytype_input)  # Save via API.
                    if result and result.get("daytype"):  # Update on success.
                        created_name = result.get("daytype")  # Stored name.
                        if created_name not in custom_daytypes:  # Avoid duplicates.
                            st.session_state["custom_daytypes"] = custom_daytypes + [created_name]  # Append.
                        st.session_state["pending_daytype_selection"] = created_name  # Select on rerun.
                        st.session_state["pending_daytype_input_clear"] = True  # Clear input on rerun.
                        safe_rerun()  # Refresh to update options.
        with top_row_right:  # Date column.
            entry_date = st.date_input(  # Date input.
                "Date",  # Label.
                value=(active_date if is_active_session else date.today()),  # Active or today.
                disabled=is_active_session,  # Lock date during active session.
                key="entry_date",  # Session key for reset support.
            )  # End date input.
    #
    # Choose the effective day type for exercise options.
        effective_daytype = active_daytype if is_active_session else entry_daytype  # Active or selected.
        effective_daytype_key = None  # Default when day type is not selected.
        if effective_daytype and effective_daytype != ADD_DAYTYPE_OPTION:  # Only normalize real day types.
            effective_daytype_key = normalize_label(effective_daytype)  # Normalize for lookups.
        if effective_daytype_key and effective_daytype_key not in st.session_state.get("custom_exercises_loaded", set()):
            custom_exercises = st.session_state.get("custom_exercises", {})  # Read cache.
            custom_exercises[effective_daytype_key] = auth.fetch_custom_exercises(effective_daytype_key)  # Fetch.
            st.session_state["custom_exercises"] = custom_exercises  # Store exercises.
            st.session_state["custom_exercises_loaded"].add(effective_daytype_key)  # Mark as loaded.
        if st.session_state.get("last_daytype_selection") != effective_daytype:  # Reset on change.
            options = build_exercise_options(  # Build options for reset.
                effective_daytype_key,  # Day type key.
                st.session_state.get("custom_exercises", {}),  # Custom exercises cache.
            )
            st.session_state["entry_exercise"] = options[0] if options else ADD_EXERCISE_OPTION  # Reset exercise.
            st.session_state["last_daytype_selection"] = effective_daytype  # Track selection.
    #
    # Exercise selector lives outside the form to allow dynamic inputs.
        custom_exercises_map = st.session_state.get("custom_exercises", {})  # Read custom exercises.
        exercise_options = build_exercise_options(  # Build exercise options.
            effective_daytype_key,  # Day type key.
            custom_exercises_map,  # Custom exercises per day type.
        )
        exercise_options_with_add = exercise_options + [ADD_EXERCISE_OPTION]  # Add custom trigger.
        pending_exercise = st.session_state.get("pending_exercise_selection")  # Pending selection.
        if pending_exercise:  # Apply pending selection before widget renders.
            st.session_state["entry_exercise"] = pending_exercise  # Update selection safely.
            st.session_state["pending_exercise_selection"] = None  # Clear pending.
        if st.session_state.get("pending_exercise_input_clear"):  # Clear input before widget.
            st.session_state["custom_exercise_input"] = ""  # Clear input safely.
            st.session_state["pending_exercise_input_clear"] = False  # Reset flag.
        entry_exercise = st.selectbox(  # Exercise input.
            "Exercise Name",  # Label.
            options=exercise_options_with_add,  # Day-specific options.
            disabled=(effective_daytype == ADD_DAYTYPE_OPTION),  # Disable until day type exists.
            key="entry_exercise",  # Session key for reset support.
        )  # End exercise selectbox.
        custom_exercise_input = ""  # Default custom exercise input.
        save_exercise_clicked = False  # Default save state.
        if entry_exercise == ADD_EXERCISE_OPTION:  # Show custom exercise input.
            exercise_input_col, exercise_button_col = st.columns([2.2, 1], gap="small")  # Input row.
            with exercise_input_col:  # Custom exercise input column.
                custom_exercise_input = st.text_input(  # Custom exercise name.
                    "Custom exercise",  # Label.
                    key="custom_exercise_input",  # Session key.
                    placeholder="e.g. incline press",  # Placeholder text.
                )
            with exercise_button_col:  # Custom exercise button column.
                save_exercise_clicked = st.button(  # Save exercise action.
                    "Save Exercise",  # Button label.
                    type="secondary",  # Secondary styling.
                    use_container_width=True,  # Match input width.
                )
    # Group the remaining input controls in a form so submissions are atomic.
        workout_form = st.form("workout_entry_form", clear_on_submit=True)  # Create a form block.
        with workout_form:  # Scope inputs to the form.
            weight_col, rep_col = st.columns([1, 1], gap="small")  # Weight/rep row.
            with weight_col:  # Weight column.
                entry_weight = st.number_input(  # Weight input.
                    "Weight (kg)",  # Label.
                    min_value=0.0,  # Minimum value.
                    step=1.0,  # Step size.
                    format="%.2f",  # Display format.
                    key="entry_weight",  # Session key for reset support.
                )
            with rep_col:  # Rep column.
                entry_rep = st.number_input(  # Reps input.
                    "Rep",  # Label.
                    min_value=0,  # Minimum value.
                    step=1,  # Step size.
                    format="%d",  # Display format.
                    key="entry_rep",  # Session key for reset support.
                )
        def reset_entry_fields():  # Reset only the current entry fields.
            options = build_exercise_options(effective_daytype_key, st.session_state.get("custom_exercises", {}))  # Read.
            st.session_state["pending_exercise_selection"] = options[0] if options else ADD_EXERCISE_OPTION  # Reset.
            st.session_state["pending_exercise_input_clear"] = True  # Clear input on rerun.
            st.session_state["entry_weight"] = 0.0  # Reset weight.
            st.session_state["entry_rep"] = 0  # Reset reps.
        def mark_add_workout_clicked():  # Persist Add Workout clicks; reruns can drop transient button state.
            st.session_state["add_workout_clicked"] = True  # Remember the click.
        add_col, reset_col = st.columns([1, 1], gap="small")  # Layout for form actions.
        with add_col:  # Left action column.
            reset_fields = st.button(  # Reset button outside the form submit.
                "Reset Fields",  # Reset label.
                type="secondary",  # Secondary styling.
                on_click=reset_entry_fields,  # Reset callback.
            )
        with reset_col:  # Right action column.
            workout_form.form_submit_button(  # Submit button.
                "Add Workout",  # Label.
                type="primary",  # Primary styling.
                on_click=mark_add_workout_clicked,  # Avoid double-click loss on rerun.
            )
    #
    # Show a button to finish the active day session.
        def mark_finish_workout_clicked():  # Persist Finish Workout clicks; avoid double-click requirement.
            st.session_state["finish_workout_clicked"] = True  # Remember the click.
        workout_rows = st.session_state.get("workout_rows", [])  # Read current entries.
        finish_disabled = (len(workout_rows) == 0)  # Disable until at least one entry is logged.
        st.button(  # End session button.
            "Finish Workout",  # Button label.
            disabled=finish_disabled,  # Disable until there is at least one entry.
            type="primary",  # Primary styling.
            use_container_width=True,  # Make the button full width on narrow screens.
            on_click=mark_finish_workout_clicked,  # Avoid double-click loss on rerun.
        )
        submitted = st.session_state.get("add_workout_clicked", False)  # Read click state for rerun-safe submit.
        finish_clicked = st.session_state.get("finish_workout_clicked", False)  # Read click state for rerun-safe finish.
        submitted = submitted and not reset_fields and not save_exercise_clicked  # Skip when other actions run.
        if save_exercise_clicked:  # Handle custom exercise creation.
            if effective_daytype == ADD_DAYTYPE_OPTION:  # Guard invalid day type.
                st.error("Save the day type before adding exercises.")  # Prompt user action.
            else:  # Persist the custom exercise.
                result = auth.add_custom_exercise(effective_daytype, custom_exercise_input)  # Save via API.
                if result and result.get("exercise"):  # Update on success.
                    exercise_name = result.get("exercise")  # Stored exercise name.
                    custom_map = st.session_state.get("custom_exercises", {})  # Read cached map.
                    custom_list = custom_map.get(effective_daytype_key, [])  # Read existing list.
                    if exercise_name not in custom_list:  # Avoid duplicates.
                        custom_map[effective_daytype_key] = custom_list + [exercise_name]  # Append.
                        st.session_state["custom_exercises"] = custom_map  # Store updated map.
                    st.session_state["pending_exercise_selection"] = exercise_name  # Select on rerun.
                    st.session_state["pending_exercise_input_clear"] = True  # Clear input on rerun.
                    safe_rerun()  # Refresh to update options.
        if submitted and entry_exercise == ADD_EXERCISE_OPTION:  # Prevent invalid submission.
            st.error("Select or save an exercise before adding a workout.")  # Warn user.
            submitted = False  # Stop submission.
        if finish_clicked:  # Handle finish flow on click.
            with status_context("Finishing workout..."):  # Visible status indicator.
                time.sleep(0.4)  # Brief delay for a smooth UI.
            last_session_id = st.session_state.get("active_session_id")  # Read session id.
            st.session_state["show_history"] = False  # Close history panel after finishing.
            st.session_state["workout_completed"] = True  # Mark workout as completed.
            if cookies_ready:  # Persist completion state when available.
                cookie_manager["workout_completed"] = "true"  # Persist completion cookie.
                queue_cookie_save()  # Commit cookie changes once.
            access_token = auth.ensure_access_token()  # Read or refresh access token.
            if access_token and last_session_id:  # Mark session as completed in Supabase.
                authed_supabase = create_client(  # Create a new client with an auth header.
                    supabase_url,  # Supabase URL.
                    supabase_key,  # Supabase anon key.
                    options=ClientOptions(headers={"Authorization": f"Bearer {access_token}"}),  # Auth header.
                )
                try:  # Attempt to set PostgREST auth header.
                    authed_supabase.postgrest.auth(access_token)  # Apply auth token.
                except Exception:  # Ignore if not supported by client.
                    pass  # Continue with update.
                try:  # Attempt to update the session completion time.
                    update_result = authed_supabase.table("workout_sessions").update(  # Update session row.
                        {"completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}  # Set timestamp.
                    ).eq("id", last_session_id).execute()  # Update by session id.
                    if not update_result.data:  # Warn when no rows were updated.
                        st.warning("Finish Workout did not update any session rows.")  # Surface warning.
                    else:  # Confirm completion timestamp.
                        confirm_result = authed_supabase.table("workout_sessions").select(  # Fetch updated row.
                            "completed_at"  # Only read completion column.
                        ).eq("id", last_session_id).execute()  # Query by session id.
                        completed_at = None  # Default completion value.
                        if confirm_result.data:  # Read completion value.
                            completed_at = confirm_result.data[0].get("completed_at")  # Extract timestamp.
                        if not completed_at:  # Warn when completion did not persist.
                            st.warning("Finish Workout completed, but completed_at is still empty.")  # Warn user.
                except Exception as exc:  # Catch update errors.
                    st.error(f"Failed to mark session complete: {exc}")  # Show error message.
            st.session_state["active_daytype"] = None  # Clear active day type.
            st.session_state["active_date"] = None  # Clear active date.
            st.session_state["active_session_id"] = None  # Clear active session id.
            st.session_state["last_session_id"] = last_session_id  # Store last session id.
            if cookies_ready:  # Persist session id when available.
                cookie_manager["last_session_id"] = last_session_id or ""  # Persist session id.
                queue_cookie_save()  # Commit cookie changes once.
            st.session_state["workout_notice"] = "Workout completed."  # Set completion message.
            st.session_state["finish_workout_clicked"] = False  # Reset click flag after handling.
            safe_rerun()  # Rerun to unlock inputs.
#
#
# Append the entry to the table when the form is submitted.
if submitted:  # Only run when the button is pressed.
    st.session_state["show_history"] = False  # Ensure history panel is closed.
    st.session_state["workout_completed"] = False  # Keep form/table mode active.
    if cookies_ready:  # Persist completion reset when available.
        cookie_manager["workout_completed"] = "false"  # Clear completion cookie.
        queue_cookie_save()  # Commit cookie changes once.
    if not is_active_session:  # Start a new session if none is active.
        st.session_state["active_daytype"] = entry_daytype  # Set active day type.
        st.session_state["active_date"] = entry_date  # Set active date.
        active_daytype = entry_daytype  # Update local active day type.
        active_date = entry_date  # Update local active date.
    # Use active values to avoid changes during a session.
    entry_daytype = active_daytype if active_daytype is not None else entry_daytype  # Lock day type.
    entry_date = active_date if active_date is not None else entry_date  # Lock date.
    st.session_state["workout_rows"].append(  # Add a new row dict.
        {
            "Date": normalize_date(entry_date),  # Store date.
            "Daytype ▼": entry_daytype,  # Store day type.
            "Exercise Name": entry_exercise,  # Store exercise.
            "Weight (kg)": entry_weight,  # Store weight.
            "Rep": entry_rep,  # Store reps.
        }
    )  # End append.
    #
    # Insert the row into Supabase when the client is available.
    if supabase is not None:  # Only insert when configured.
        access_token = auth.ensure_access_token()  # Read or refresh access token.
        if not access_token:  # Warn when no auth token is available.
            st.error("You are not authenticated for inserts. Please log in again.")  # Show error.
        else:  # Proceed with authenticated inserts.
            # Build an authenticated Supabase client for row inserts.
            authed_supabase = create_client(  # Create a new client with an auth header.
                supabase_url,  # Supabase URL.
                supabase_key,  # Supabase anon key.
                options=ClientOptions(headers={"Authorization": f"Bearer {access_token}"}),  # Auth header.
            )
            try:  # Attempt to set PostgREST auth header.
                authed_supabase.postgrest.auth(access_token)  # Apply auth token.
            except Exception:  # Ignore if not supported by client.
                pass  # Continue with insert.
            user_id = None  # Default user id.
            if st.session_state.get("user"):  # Read user id from session user.
                user_id = getattr(st.session_state["user"], "id", None)  # Read attribute id.
            if user_id is None and isinstance(st.session_state.get("user"), dict):  # Read dict user id.
                user_id = st.session_state["user"].get("id")  # Read dict id.
            session_id = st.session_state.get("active_session_id")  # Read active session id.
            if not session_id:  # Create a new session when none is active.
                session_insert = authed_supabase.table("workout_sessions").insert(  # Insert session.
                    {
                        "user_id": user_id,  # User id column in Supabase.
                        "date": entry_date.isoformat(),  # Session date.
                        "daytype": entry_daytype,  # Session day type.
                    }
                ).execute()  # Execute insert.
                if session_insert.data:  # Read session id from response.
                    session_id = session_insert.data[0].get("id")  # Extract session id.
                else:  # Fallback to fetch the latest session for this day.
                    latest_session = authed_supabase.table("workout_sessions").select("id").eq(  # Query session.
                        "user_id", user_id  # Filter by user id.
                    ).eq(  # Filter by date.
                        "date", entry_date.isoformat()  # Session date.
                    ).eq(  # Filter by day type.
                        "daytype", entry_daytype  # Session day type.
                    ).order(  # Get latest session for this key.
                        "created_at", desc=True
                    ).limit(1).execute()  # Execute lookup.
                    if latest_session.data:  # Read session id if found.
                        session_id = latest_session.data[0].get("id")  # Extract session id.
                if session_id:  # Persist the active session id.
                    st.session_state["active_session_id"] = session_id  # Store active session id.
            if session_id:  # Insert the workout entry for the session.
                try:  # Attempt to insert the workout entry.
                    authed_supabase.table("workout_entries").insert(  # Insert entry row.
                        {
                            "session_id": session_id,  # Link to session.
                            "exercise_name": entry_exercise,  # Exercise column in Supabase.
                            "weight": entry_weight,  # Weight column in Supabase.
                            "rep": entry_rep,  # Rep column in Supabase.
                        }
                    ).execute()  # Execute the insert.
                except Exception as exc:  # Catch insert errors.
                    st.error(f"Database insert failed: {exc}")  # Show error message.
    st.session_state["add_workout_clicked"] = False  # Reset click flag after handling.
else:  # Ensure click flags do not persist across reruns.
    st.session_state["add_workout_clicked"] = False  # Clear stale click state.
#
# Create a DataFrame for display.
workout_table = pd.DataFrame(st.session_state["workout_rows"])  # Build table.
#
# Show the table, centered when the form is hidden.
if not workout_table.empty and not st.session_state.get("show_history"):  # Skip table on history view.
    if show_form:  # Keep the table on the right during entry.
        with right_col:  # Scope the table to the right column.
            st.caption("Recent entries")  # Table header caption.
            recent_rows = workout_table.tail(10)  # Show latest entries by default.
            recent_height = 36 + min(len(recent_rows), 10) * 35  # Fit rows without empty space.
            render_dataframe(recent_rows, recent_height)  # Render the compact table.
            with st.expander("Show all entries"):  # Expand for full history.
                full_height = 36 + min(len(workout_table), 18) * 35  # Fit rows without empty space.
                render_dataframe(workout_table, full_height)  # Render the full table.
    else:  # Center the table horizontally when the form is hidden.
        _, center_col, _ = st.columns([0.4, 3.2, 0.4])  # Create centered column layout.
        with center_col:  # Scope the table to the center column.
            st.caption("Workout summary")  # Table header caption.
            summary_height = 36 + min(len(workout_table), 12) * 35  # Fit rows without empty space.
            render_dataframe(workout_table, summary_height)  # Render the table.
            st.button(  # Button to return to the home page.
                "Done",  # Button label.
                type="primary",  # Primary styling.
                on_click=lambda: st.session_state.update({"done_clicked": True}),  # Persist click across reruns.
            )
elif not show_form:  # Handle missing summary after completion.
    st.info("Summary not available yet.")  # Inform the user.
    st.button(  # Button to return to the home page.
        "Done",  # Button label.
        type="primary",  # Primary styling.
        on_click=lambda: st.session_state.update({"done_clicked": True}),  # Persist click across reruns.
    )

if st.session_state.get("done_clicked"):  # Handle Done click after rerun-safe button.
    st.session_state["workout_completed"] = False  # Clear completion state.
    st.session_state["workout_rows"] = []  # Clear summary rows.
    st.session_state["active_session_id"] = None  # Clear active session id.
    st.session_state["active_daytype"] = None  # Clear active day type.
    st.session_state["active_date"] = None  # Clear active date.
    st.session_state["show_history"] = False  # Close history panel.
    st.session_state.pop("history_data", None)  # Clear history data.
    if cookies_ready:  # Clear completion cookie when available.
        cookie_manager.pop("workout_completed", None)  # Clear completion cookie.
        queue_cookie_save()  # Commit cookie changes once.
    st.session_state["done_clicked"] = False  # Reset click flag after handling.
    safe_rerun()  # Rerun to show the form.

# Perform a single cookie save per script run when queued.
if st.session_state.get("pending_cookie_save"):  # Check for pending saves.
    if not st.session_state.get("cookie_save_ran"):  # Guard against duplicate saves.
        st.session_state["cookie_save_ran"] = True  # Mark save as done.
        st.session_state["pending_cookie_save"] = False  # Clear save flag.
        cookie_manager.save()  # Commit cookie changes.

# Mobile scroll spacer to ensure bottom buttons are reachable.
st.markdown("<div style='height: 160px;'></div>", unsafe_allow_html=True)  # Bottom spacer.
