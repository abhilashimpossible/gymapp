# Import FastAPI primitives for building the API.
from fastapi import FastAPI  # FastAPI app.
# Import auth and history routers.
from backend.auth_routes import router as auth_router  # Auth endpoints.
from backend.history_api import router as history_router  # History endpoints.
# Import customization endpoints.
from backend.customizations_api import router as customizations_router  # Customization endpoints.

# Create the FastAPI application instance.
app = FastAPI(title="Workout API")  # FastAPI app metadata.

# Register auth routes at the root.
app.include_router(auth_router)  # Add auth endpoints.
# Register history routes at the root.
app.include_router(history_router)  # Add history endpoints.
# Register customization routes at the root.
app.include_router(customizations_router)  # Add customization endpoints.

# Health check endpoint for uptime monitoring.
@app.get("/health", tags=["health"])  # Health endpoint with tag.
def health_check():  # Simple health handler.
    return {"status": "ok"}  # Return basic health payload.
