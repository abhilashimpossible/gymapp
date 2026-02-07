# Import FastAPI primitives for building the API.
from fastapi import APIRouter, HTTPException  # Router and errors.
# Import JSON encoder for complex objects.
from fastapi.encoders import jsonable_encoder  # Convert objects to JSON-safe data.
# Import JSON response helpers.
from fastapi.responses import JSONResponse  # Structured JSON responses.
# Import request body validation.
from pydantic import BaseModel, EmailStr  # Email validation for payloads.
# Import the shared Supabase client.
from backend.db_client import supabase  # Supabase client instance.

# Create a router for auth endpoints.
router = APIRouter(tags=["auth"])  # Router instance with tags.

# Define the expected request body for auth endpoints.
class AuthPayload(BaseModel):  # Payload schema for auth.
    email: EmailStr  # Email address.
    password: str  # Password string.
    name: str | None = None  # Optional display name.

# Validate that Supabase is configured.
def _require_supabase():  # Guard helper.
    if supabase is None:  # Check client availability.
        raise HTTPException(status_code=500, detail="Supabase client is not configured.")  # Fail fast.

# Handle user signup.
@router.post("/signup")  # Signup endpoint.
def signup(payload: AuthPayload):  # Create a new user.
    _require_supabase()  # Ensure Supabase is ready.
    try:  # Attempt to sign up.
        result = supabase.auth.sign_up(  # Signup call.
            {  # Build signup payload.
                "email": payload.email,  # Email value.
                "password": payload.password,  # Password value.
                "options": {"data": {"name": payload.name}} if payload.name else {},  # Optional name metadata.
            }
        )
        return JSONResponse(  # Return success payload.
            status_code=200,  # HTTP OK.
            content={  # Response data.
                "success": True,  # Success flag.
                "user": jsonable_encoder(result.user),  # JSON-safe user payload.
                "session": jsonable_encoder(result.session),  # JSON-safe session payload.
            },
        )
    except Exception as exc:  # Catch errors.
        raise HTTPException(status_code=400, detail=f"Signup failed: {exc}")  # Error response.

# Handle user login.
@router.post("/login")  # Login endpoint.
def login(payload: AuthPayload):  # Sign in a user.
    _require_supabase()  # Ensure Supabase is ready.
    try:  # Attempt to sign in.
        result = supabase.auth.sign_in_with_password({"email": payload.email, "password": payload.password})  # Login.
        return JSONResponse(  # Return success payload.
            status_code=200,  # HTTP OK.
            content={  # Response data.
                "success": True,  # Success flag.
                "user": jsonable_encoder(result.user),  # JSON-safe user payload.
                "session": jsonable_encoder(result.session),  # JSON-safe session payload.
            },
        )
    except Exception as exc:  # Catch errors.
        raise HTTPException(status_code=400, detail=f"Login failed: {exc}")  # Error response.

# Handle user logout.
@router.post("/logout")  # Logout endpoint.
def logout():  # Sign out a user.
    _require_supabase()  # Ensure Supabase is ready.
    try:  # Attempt to sign out.
        supabase.auth.sign_out()  # Logout call.
        return JSONResponse(  # Return success payload.
            status_code=200,  # HTTP OK.
            content={"success": True, "message": "Logged out."},  # Response data.
        )
    except Exception as exc:  # Catch errors.
        raise HTTPException(status_code=400, detail=f"Logout failed: {exc}")  # Error response.
