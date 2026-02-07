# Import FastAPI primitives for dependencies and errors.
from fastapi import Header, HTTPException  # Header parsing and errors.
# Import the shared Supabase client.
from backend.db_client import supabase  # Supabase client instance.

# Resolve the current user from the Authorization header.
def get_current_user(authorization: str | None = Header(default=None)):  # Read auth header.
    if supabase is None:  # Guard when Supabase is not configured.
        raise HTTPException(status_code=500, detail="Supabase client is not configured.")  # Fail fast.
    if not authorization:  # Require a token.
        raise HTTPException(status_code=401, detail="Authorization header missing.")  # Unauthorized.
    token = authorization.replace("Bearer ", "", 1) if authorization.startswith("Bearer ") else authorization  # Token.
    try:  # Attempt to fetch the user from Supabase.
        result = supabase.auth.get_user(token)  # Resolve user from token.
        user = result.user if hasattr(result, "user") else result  # Normalize user object.
        if user is None:  # Guard when user is missing.
            raise HTTPException(status_code=401, detail="Invalid auth token.")  # Unauthorized.
        return user  # Return resolved user.
    except Exception as exc:  # Catch and normalize errors.
        raise HTTPException(status_code=401, detail=f"Invalid auth token: {exc}")  # Unauthorized.
