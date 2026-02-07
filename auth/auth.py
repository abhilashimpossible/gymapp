# Import Streamlit for session state and messages.
import streamlit as st  # Streamlit primitives.
# Import HTTP client for auth API calls.
import requests  # HTTP requests to FastAPI.
# Import environment access for API URL.
import os  # Read environment variables.

# =========================
# Supabase Client Section
# =========================
# Store a Supabase client reference in the module.
supabase = None  # Will be set from app.py.
# Store a cookie manager reference in the module.
cookies = None  # Will be set from app.py.
# Store an auth API base URL.
auth_api_url = None  # Will be set from app.py or environment.

# Check whether cookies are ready.
def _cookies_ready():  # Verify cookie readiness.
    if cookies is None:  # No cookie manager.
        return False  # Not ready.
    ready_attr = getattr(cookies, "ready", None)  # Read readiness method.
    if callable(ready_attr):  # Use ready() when available.
        return cookies.ready()  # Return readiness state.
    return False  # Default to not ready.

# Save cookies at most once per script run.
def _safe_cookie_save():  # Guard cookie saves.
    if not _cookies_ready():  # Only save when ready.
        return  # Exit when cookies are unavailable.
    if st.session_state.get("cookie_save_ran"):  # Skip duplicate saves.
        return  # Already saved this run.
    st.session_state["cookie_save_ran"] = True  # Mark as saved.
    cookies.save()  # Commit cookie changes.

# =========================
# Session Helpers
# =========================
# Store the user object and a display email in session state.
def _store_user(user, fallback_email=None, fallback_name=None, session=None):  # Persist user info.
    st.session_state["user"] = user  # Store the raw user object.
    user_email = None  # Default email value.
    user_name = None  # Default name value.
    if user is not None:  # Extract email from the user object.
        user_email = getattr(user, "email", None)  # Read attribute email.
        user_metadata = getattr(user, "user_metadata", None)  # Read user metadata.
        if user_metadata and isinstance(user_metadata, dict):  # Read metadata name.
            user_name = user_metadata.get("name")  # Read name from metadata.
        if user_email is None and isinstance(user, dict):  # Handle dict users.
            user_email = user.get("email")  # Read dict email.
            user_name = user.get("user_metadata", {}).get("name")  # Read dict name.
    if user_email is None:  # Fall back to provided email if needed.
        user_email = fallback_email  # Use fallback email.
    if user_name is None:  # Fall back to provided name if needed.
        user_name = fallback_name  # Use fallback name.
    if user_email:  # Store email when available.
        st.session_state["user_email"] = user_email  # Persist email.
    if user_name:  # Store name when available.
        st.session_state["user_name"] = user_name  # Persist name.
    if session is not None:  # Store session tokens when available.
        if isinstance(session, dict):  # Handle dict session payloads.
            st.session_state["access_token"] = session.get("access_token")  # Store access token.
            st.session_state["refresh_token"] = session.get("refresh_token")  # Store refresh token.
        else:  # Handle client session objects.
            st.session_state["access_token"] = getattr(session, "access_token", None)  # Store access token.
            st.session_state["refresh_token"] = getattr(session, "refresh_token", None)  # Store refresh token.
        if _cookies_ready():  # Persist tokens in cookies when available.
            cookies["access_token"] = st.session_state["access_token"]  # Save access token cookie.
            cookies["refresh_token"] = st.session_state["refresh_token"]  # Save refresh token cookie.
            _safe_cookie_save()  # Commit cookie changes.

# Build the auth API base URL.
def _get_auth_api_url():  # Read auth API URL.
    if auth_api_url:  # Prefer explicit configuration.
        return auth_api_url  # Use configured URL.
    return os.getenv("AUTH_API_URL", "http://localhost:8000")  # Default to local.

# Call the auth API endpoint.
def _call_auth_api(path, payload=None):  # Make API requests.
    url = f"{_get_auth_api_url().rstrip('/')}{path}"  # Build the endpoint URL.
    response = requests.post(url, json=payload, timeout=15)  # Perform the request.
    if not response.ok:  # Raise a clear error on failure.
        raise Exception(response.json().get("detail", response.text))  # Surface API error.
    return response.json()  # Return JSON payload.

# =========================
# History API Section
# =========================
# Resolve the access token for authenticated requests.
def _get_access_token():  # Read access token for API calls.
    token = st.session_state.get("access_token")  # Check session state first.
    if not token and _cookies_ready():  # Fall back to cookies when available.
        token = cookies.get("access_token")  # Read access token cookie.
    return token  # Return token value.

# Ensure a valid access token by refreshing when possible.
def ensure_access_token():  # Refresh access token when expired.
    if supabase is None:  # Guard when Supabase is not configured.
        return _get_access_token()  # Fall back to stored token.
    access_token = _get_access_token()  # Read current access token.
    refresh_token = st.session_state.get("refresh_token")  # Read refresh token.
    if not refresh_token and _cookies_ready():  # Fall back to cookie refresh token.
        refresh_token = cookies.get("refresh_token")  # Read refresh token cookie.
    if not refresh_token:  # Return current token when refresh is unavailable.
        return access_token  # Return existing token.
    try:  # Attempt to refresh the session.
        result = supabase.auth.refresh_session(refresh_token)  # Refresh session.
        if getattr(result, "session", None):  # Store refreshed session data.
            _store_user(result.user, session=result.session)  # Persist refreshed tokens.
            return result.session.access_token  # Return refreshed access token.
    except Exception:  # Ignore refresh errors and fall back.
        return access_token  # Return existing token.
    return access_token  # Default to current token.

# Fetch workout history from the backend API.
def fetch_history(period=None, from_date=None, to_date=None):  # Read workout history.
    token = _get_access_token()  # Resolve the access token.
    if not token:  # Guard when token is missing.
        st.error("Please log in again to view workout history.")  # Prompt re-login.
        return None  # Stop when unauthenticated.
    url = f"{_get_auth_api_url().rstrip('/')}/history"  # Build history endpoint.
    params = {}  # Start query parameters.
    if period:  # Include period when provided.
        params["period"] = period  # Add period filter.
    if from_date:  # Include from_date when provided.
        params["from_date"] = from_date  # Add start date filter.
    if to_date:  # Include to_date when provided.
        params["to_date"] = to_date  # Add end date filter.
    headers = {"Authorization": f"Bearer {token}"}  # Attach auth header.
    response = requests.get(url, params=params, headers=headers, timeout=15)  # Perform request.
    if not response.ok:  # Surface errors from the API.
        try:  # Try to parse JSON error payload.
            error_detail = response.json().get("detail", "Unable to load history.")  # Read JSON detail.
        except ValueError:  # Handle non-JSON responses.
            error_detail = response.text or "Unable to load history."  # Fallback to raw text.
        st.error(error_detail)  # Show error.
        return None  # Stop on error.
    return response.json()  # Return history payload.

# =========================
# Session Restore Section
# =========================
# Restore a session from tokens saved in session state.
def restore_session():  # Restore session across refreshes.
    if supabase is None:  # Guard when Supabase is not configured.
        return  # Exit early.
    if st.session_state.get("user"):  # Skip when user is already set.
        return  # Exit early.
    access_token = st.session_state.get("access_token")  # Read stored access token.
    refresh_token = st.session_state.get("refresh_token")  # Read stored refresh token.
    if _cookies_ready() and (not access_token or not refresh_token):  # Load from cookies if missing.
        access_token = cookies.get("access_token")  # Read access token cookie.
        refresh_token = cookies.get("refresh_token")  # Read refresh token cookie.
    if access_token and refresh_token:  # Only restore when both tokens exist.
        try:  # Attempt to set the session.
            result = supabase.auth.set_session(access_token, refresh_token)  # Restore session.
            _store_user(result.user, session=result.session)  # Persist restored user.
        except Exception:  # Ignore restore errors and fall back to login.
            st.session_state.pop("access_token", None)  # Clear bad access token.
            st.session_state.pop("refresh_token", None)  # Clear bad refresh token.
            if _cookies_ready():  # Clear bad cookies as well.
                cookies.pop("access_token", None)  # Remove access token cookie.
                cookies.pop("refresh_token", None)  # Remove refresh token cookie.
                _safe_cookie_save()  # Commit cookie changes.

# =========================
# Query Param Helpers
# =========================
# Read query parameters in a Streamlit-compatible way.
def _get_query_params():  # Read query params safely.
    if hasattr(st, "query_params"):  # Use modern Streamlit API when available.
        return dict(st.query_params)  # Return query params as a dict.
    return st.experimental_get_query_params()  # Fallback for older versions.

# Clear query parameters after processing a callback.
def _clear_query_params():  # Clear query params safely.
    if hasattr(st, "query_params"):  # Use modern Streamlit API when available.
        st.query_params.clear()  # Clear all query params.
    else:  # Fallback for older versions.
        st.experimental_set_query_params()  # Clear all query params.

# Trigger a rerun to return to the main page after confirmation.
def _rerun_app():  # Rerun the app safely.
    if hasattr(st, "rerun"):  # Use modern Streamlit API when available.
        st.rerun()  # Rerun the app.
    else:  # Fallback for older versions.
        st.experimental_rerun()  # Rerun the app.

# =========================
# Auth Callback Section
# =========================
# Handle Supabase email confirmation or magic link callbacks.
def handle_auth_callback():  # Process auth callback from URL.
    if supabase is None:  # Guard when Supabase is not configured.
        return  # Exit early when no client is available.
    params = _get_query_params()  # Read the query parameters.
    token = params.get("token")  # Read token used for email verification.
    action = params.get("type") or params.get("action")  # Read action type.
    access_token = params.get("access_token")  # Read access token if present.
    refresh_token = params.get("refresh_token")  # Read refresh token if present.
    if isinstance(token, list):  # Normalize list values to a scalar.
        token = token[0]  # Use the first token value.
    if isinstance(action, list):  # Normalize list values to a scalar.
        action = action[0]  # Use the first action value.
    if isinstance(access_token, list):  # Normalize list values to a scalar.
        access_token = access_token[0]  # Use the first access token value.
    if isinstance(refresh_token, list):  # Normalize list values to a scalar.
        refresh_token = refresh_token[0]  # Use the first refresh token value.
    if token and action:  # Handle email confirmation callbacks.
        try:  # Attempt to verify the token.
            result = supabase.auth.verify_otp({"token": token, "type": action})  # Verify OTP.
            _store_user(result.user, session=result.session)  # Store the user in session state.
            st.session_state["auth_notice"] = "Email confirmed and logged in."  # Store notice.
            _clear_query_params()  # Clear the callback parameters.
            _rerun_app()  # Redirect back to the main page.
        except Exception as exc:  # Catch verification errors.
            st.error(f"Confirmation failed: {exc}")  # Show error message.
    elif access_token and refresh_token:  # Handle session tokens in the URL.
        try:  # Attempt to set the session.
            result = supabase.auth.set_session(access_token, refresh_token)  # Set auth session.
            _store_user(result.user, session=result.session)  # Store the user in session state.
            st.session_state["auth_notice"] = "Session restored."  # Store notice.
            _clear_query_params()  # Clear the callback parameters.
            _rerun_app()  # Redirect back to the main page.
        except Exception as exc:  # Catch session errors.
            st.error(f"Session restore failed: {exc}")  # Show error message.

# =========================
# Auth Action Section
# =========================
# Handle user signup against Supabase Auth.
def handle_signup(email: str, password: str, name: str | None = None):  # Signup entry point.
    try:  # Attempt signup.
        payload = {"email": email, "password": password, "name": name}  # Build signup payload.
        data = _call_auth_api("/signup", payload)  # Call backend signup endpoint.
        st.session_state["user"] = None  # Keep user logged out after signup.
        st.session_state.pop("user_email", None)  # Clear stored email.
        st.session_state.pop("user_name", None)  # Clear stored name.
        st.session_state.pop("access_token", None)  # Clear stored access token.
        st.session_state.pop("refresh_token", None)  # Clear stored refresh token.
        st.session_state["welcome_shown"] = False  # Reset welcome flag.
        st.session_state["auth_notice"] = "Signup successful. Please log in to continue."  # Notice.
        _rerun_app()  # Rerun to refresh the UI.
    except Exception as exc:  # Catch any auth errors.
        st.error(f"Signup failed: {exc}")  # Show error message.

# Handle user login against Supabase Auth.
def handle_login(email: str, password: str):  # Login entry point.
    try:  # Attempt login.
        payload = {"email": email, "password": password}  # Build login payload.
        data = _call_auth_api("/login", payload)  # Call backend login endpoint.
        _store_user(data.get("user"), fallback_email=email, session=data.get("session"))  # Store user.
        st.session_state["welcome_shown"] = False  # Allow welcome message once.
        st.session_state["auth_notice"] = "Logged in successfully."  # Notice.
        _rerun_app()  # Rerun to refresh the UI.
    except Exception as exc:  # Catch any auth errors.
        st.error(f"Login failed: {exc}")  # Show error message.

# Handle user logout against Supabase Auth.
def handle_logout():  # Logout entry point.
    try:  # Attempt logout.
        _call_auth_api("/logout", None)  # Call backend logout endpoint.
        st.session_state["user"] = None  # Clear the user in session state.
        st.session_state.pop("user_email", None)  # Clear stored email.
        st.session_state.pop("user_name", None)  # Clear stored name.
        st.session_state.pop("access_token", None)  # Clear stored access token.
        st.session_state.pop("refresh_token", None)  # Clear stored refresh token.
        if _cookies_ready():  # Clear stored cookies.
            cookies.pop("access_token", None)  # Remove access token cookie.
            cookies.pop("refresh_token", None)  # Remove refresh token cookie.
            _safe_cookie_save()  # Commit cookie changes.
        st.session_state["auth_notice"] = "Logged out successfully."  # Notice.
        _rerun_app()  # Rerun to refresh the UI.
    except Exception as exc:  # Catch any auth errors.
        st.error(f"Logout failed: {exc}")  # Show error message.
