# Import FastAPI router and dependency helper.
from fastapi import APIRouter, Depends, Header, HTTPException, Query  # Router, deps, headers.
# Import request validation.
from pydantic import BaseModel  # Payload validation.
# Import typing helpers.
from typing import Optional  # Optional typing.
# Import Supabase client factory.
from supabase import create_client, ClientOptions  # Authed Supabase client.
# Import shared Supabase configuration.
from backend.db_client import SUPABASE_KEY, SUPABASE_URL, supabase  # Supabase client instance.
# Import the authentication dependency.
from backend.auth import get_current_user  # Resolve the current user.

# Create a router for customization endpoints.
router = APIRouter(tags=["customizations"])  # Router instance with tags.

# Define predefined day types to prevent duplicate custom entries.
PREDEFINED_DAYTYPES = {"push", "pull", "leg", "arm"}  # Built-in day types.


def _normalize(value: str) -> str:  # Normalize names for case-insensitive uniqueness.
    return value.strip().lower()  # Trim and lowercase input.


def _authed_supabase(token: Optional[str]):  # Build an authed Supabase client.
    if token:  # Create client when token exists.
        client = create_client(  # Build client with auth header.
            SUPABASE_URL,  # Supabase URL.
            SUPABASE_KEY,  # Supabase anon key.
            options=ClientOptions(headers={"Authorization": f"Bearer {token}"}),  # Auth header.
        )
        try:  # Attempt to set PostgREST auth header.
            client.postgrest.auth(token)  # Apply auth token.
        except Exception:  # Ignore if not supported by client.
            pass  # Continue with authed client.
        return client  # Return authed client.
    return supabase  # Fall back to shared client.


class DaytypePayload(BaseModel):  # Payload for creating day types.
    name: str  # Day type name.


class ExercisePayload(BaseModel):  # Payload for creating exercises.
    daytype: str  # Associated day type.
    name: str  # Exercise name.


@router.get("/daytypes")  # Register GET /daytypes.
def list_daytypes(  # Return custom day types for the user.
    user=Depends(get_current_user),  # Require authenticated user.
    authorization: Optional[str] = Header(default=None),  # Read auth header for RLS.
):
    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)  # User id.
    token = authorization.replace("Bearer ", "", 1) if authorization else ""  # Extract token.
    client = _authed_supabase(token)  # Build authed client.
    result = client.table("user_daytypes").select("daytype_name, daytype_key").eq(  # Query day types.
        "user_id", user_id  # Filter by user id.
    ).order("daytype_name").execute()  # Execute query.
    daytypes = [row.get("daytype_name") for row in (result.data or [])]  # Extract names.
    return {"daytypes": daytypes}  # Return list payload.


@router.post("/daytypes")  # Register POST /daytypes.
def create_daytype(  # Create a new custom day type.
    payload: DaytypePayload,  # Request payload.
    user=Depends(get_current_user),  # Require authenticated user.
    authorization: Optional[str] = Header(default=None),  # Read auth header for RLS.
):
    name = payload.name.strip()  # Normalize whitespace.
    if not name:  # Guard against empty input.
        raise HTTPException(status_code=400, detail="Day type name is required.")  # Invalid input.
    daytype_key = _normalize(name)  # Normalize for uniqueness.
    if daytype_key in PREDEFINED_DAYTYPES:  # Prevent duplicates with built-ins.
        raise HTTPException(status_code=400, detail="That day type already exists.")  # Reject duplicates.
    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)  # User id.
    token = authorization.replace("Bearer ", "", 1) if authorization else ""  # Extract token.
    client = _authed_supabase(token)  # Build authed client.
    existing = client.table("user_daytypes").select("daytype_name").eq(  # Check for duplicates.
        "user_id", user_id
    ).eq("daytype_key", daytype_key).limit(1).execute()  # Execute query.
    if existing.data:  # Return existing entry.
        return {"daytype": existing.data[0].get("daytype_name"), "created": False}  # Idempotent response.
    insert = client.table("user_daytypes").insert(  # Insert new day type.
        {"user_id": user_id, "daytype_name": name, "daytype_key": daytype_key}
    ).execute()  # Execute insert.
    created_name = name  # Default to request name.
    if insert.data:  # Prefer stored value.
        created_name = insert.data[0].get("daytype_name", name)  # Read stored name.
    return {"daytype": created_name, "created": True}  # Return created payload.


@router.get("/exercises")  # Register GET /exercises.
def list_exercises(  # Return custom exercises for the user and day type.
    daytype: str = Query(..., description="Day type to filter exercises."),  # Required day type.
    user=Depends(get_current_user),  # Require authenticated user.
    authorization: Optional[str] = Header(default=None),  # Read auth header for RLS.
):
    daytype_key = _normalize(daytype)  # Normalize day type key.
    if not daytype_key:  # Guard against empty day type.
        raise HTTPException(status_code=400, detail="Day type is required.")  # Invalid input.
    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)  # User id.
    token = authorization.replace("Bearer ", "", 1) if authorization else ""  # Extract token.
    client = _authed_supabase(token)  # Build authed client.
    result = client.table("user_exercises").select("exercise_name, exercise_key").eq(  # Query exercises.
        "user_id", user_id
    ).eq("daytype_key", daytype_key).order("exercise_name").execute()  # Execute query.
    exercises = [row.get("exercise_name") for row in (result.data or [])]  # Extract names.
    return {"daytype": daytype_key, "exercises": exercises}  # Return list payload.


@router.post("/exercises")  # Register POST /exercises.
def create_exercise(  # Create a new custom exercise for a day type.
    payload: ExercisePayload,  # Request payload.
    user=Depends(get_current_user),  # Require authenticated user.
    authorization: Optional[str] = Header(default=None),  # Read auth header for RLS.
):
    name = payload.name.strip()  # Normalize whitespace.
    daytype_key = _normalize(payload.daytype)  # Normalize day type.
    if not name or not daytype_key:  # Guard against invalid input.
        raise HTTPException(status_code=400, detail="Day type and exercise name are required.")  # Invalid input.
    exercise_key = _normalize(name)  # Normalize exercise name.
    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)  # User id.
    token = authorization.replace("Bearer ", "", 1) if authorization else ""  # Extract token.
    client = _authed_supabase(token)  # Build authed client.
    if daytype_key not in PREDEFINED_DAYTYPES:  # Ensure custom day type exists.
        daytype_check = client.table("user_daytypes").select("id").eq(  # Verify day type.
            "user_id", user_id
        ).eq("daytype_key", daytype_key).limit(1).execute()  # Execute query.
        if not daytype_check.data:  # Reject unknown day types.
            raise HTTPException(status_code=400, detail="Unknown day type.")  # Invalid day type.
    existing = client.table("user_exercises").select("exercise_name").eq(  # Check duplicates.
        "user_id", user_id
    ).eq("daytype_key", daytype_key).eq("exercise_key", exercise_key).limit(1).execute()  # Execute query.
    if existing.data:  # Return existing entry.
        return {"exercise": existing.data[0].get("exercise_name"), "created": False, "daytype": daytype_key}
    insert = client.table("user_exercises").insert(  # Insert new exercise.
        {
            "user_id": user_id,
            "daytype_key": daytype_key,
            "exercise_name": name,
            "exercise_key": exercise_key,
        }
    ).execute()  # Execute insert.
    created_name = name  # Default to request name.
    if insert.data:  # Prefer stored value.
        created_name = insert.data[0].get("exercise_name", name)  # Read stored name.
    return {"exercise": created_name, "created": True, "daytype": daytype_key}  # Return payload.
