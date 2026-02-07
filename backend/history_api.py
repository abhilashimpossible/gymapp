# Import FastAPI router and dependency helper.
from fastapi import APIRouter, Depends  # Router and dependency injection.
# Import datetime helpers for date range calculations.
from datetime import date, timedelta  # Date math for periods.
# Import calendar helpers for month boundaries.
import calendar  # Month length helpers.
# Import counters for grouping results.
from collections import Counter  # Count sessions per day.
# Import FastAPI header parsing for auth tokens.
from fastapi import Header  # Read Authorization header.
# Import Supabase client factory for authed queries.
from supabase import create_client, ClientOptions  # Create authed client.
# Import typing for optional query parameters.
from typing import Optional  # Optional typing for query params.
# Import the shared Supabase client.
from backend.db_client import SUPABASE_KEY, SUPABASE_URL, supabase  # Supabase client instance.
# Import the authentication dependency.
from backend.auth import get_current_user  # Resolve the current user.

# Create a router for history endpoints.
router = APIRouter(tags=["history"])  # Router instance with tags.

# Define the workout history endpoint.
@router.get("/history")  # Register GET /history.
def get_history(  # Handler for history requests.
    period: Optional[str] = None,  # Optional preset range.
    from_date: Optional[str] = None,  # Optional start date (YYYY-MM-DD).
    to_date: Optional[str] = None,  # Optional end date (YYYY-MM-DD).
    user=Depends(get_current_user),  # Require authenticated user.
    authorization: Optional[str] = Header(default=None),  # Read auth header for RLS.
):
    # Resolve the user id from the auth payload.
    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)  # User id.
    # Compute date range from period when provided.
    if period:  # Use preset period ranges.
        today = date.today()  # Today’s date.
        if period == "week":  # Last 7 days.
            from_date = (today - timedelta(days=7)).isoformat()  # Start date.
            to_date = today.isoformat()  # End date is today.
        elif period == "month":  # Current calendar month.
            from_date = date(today.year, today.month, 1).isoformat()  # Start date.
            last_day = calendar.monthrange(today.year, today.month)[1]  # Month end day.
            to_date = date(today.year, today.month, last_day).isoformat()  # End date.
        elif period == "year":  # Current calendar year.
            from_date = date(today.year, 1, 1).isoformat()  # Start date.
            to_date = date(today.year, 12, 31).isoformat()  # End date.

    # Build an authed Supabase client for RLS-aware queries.
    token = authorization.replace("Bearer ", "", 1) if authorization else ""  # Extract token.
    authed_supabase = supabase  # Default to shared client.
    if token:  # Create authed client when token exists.
        authed_supabase = create_client(  # Build client with auth header.
            SUPABASE_URL,  # Supabase URL.
            SUPABASE_KEY,  # Supabase anon key.
            options=ClientOptions(headers={"Authorization": f"Bearer {token}"}),  # Auth header.
        )
        try:  # Attempt to set PostgREST auth header.
            authed_supabase.postgrest.auth(token)  # Apply auth token.
        except Exception:  # Ignore if not supported by client.
            pass  # Continue with authed client.

    # Fetch session dates and completion status for grouping.
    sessions_query = authed_supabase.table("workout_sessions").select("date, completed_at").eq("user_id", user_id)  # Base.
    if from_date:  # Apply optional start date.
        sessions_query = sessions_query.gte("date", from_date)  # Start date filter.
    if to_date:  # Apply optional end date.
        sessions_query = sessions_query.lte("date", to_date)  # End date filter.
    sessions_result = sessions_query.execute()  # Execute the sessions query.
    sessions = [row for row in (sessions_result.data or []) if row.get("completed_at")]  # Completed sessions.
    dates = [row["date"] for row in sessions]  # Collect dates.
    total_sessions = len(sessions)  # Total completed sessions.
    total_days = len(set(dates))  # Count distinct days.
    sessions_by_day = [  # Build per-day counts.
        {"date": day, "count": count} for day, count in sorted(Counter(dates).items())
    ]

    # Return the summarized history payload.
    return {  # JSON response.
        "total_sessions": total_sessions,  # Total sessions count.
        "total_days": total_days,  # Total days worked out.
        "sessions_by_day": sessions_by_day,  # Per-day counts.
    }
