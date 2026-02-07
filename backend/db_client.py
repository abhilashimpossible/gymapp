# Import environment access for secrets.
import os  # Read environment variables.
# Import TOML reader for local secrets fallback.
import tomllib  # Parse TOML secrets when env vars are missing.
# Import filesystem helpers for locating secrets.
from pathlib import Path  # Resolve local secrets file path.
# Import Supabase client factory.
from supabase import create_client  # Supabase client creation.

# Read Supabase credentials from environment variables first.
SUPABASE_URL = os.getenv("SUPABASE_URL", "")  # Supabase URL.
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")  # Supabase anon key.

# Fall back to Streamlit secrets when env vars are missing.
if not SUPABASE_URL or not SUPABASE_KEY:  # Check if any env var is missing.
    secrets_path = Path(__file__).resolve().parents[1] / ".streamlit" / "secrets.toml"  # Secrets path.
    if secrets_path.is_file():  # Only read when the file exists.
        secrets_data = tomllib.loads(secrets_path.read_text())  # Parse the secrets file.
        SUPABASE_URL = SUPABASE_URL or secrets_data.get("SUPABASE_URL", "")  # Fill from secrets.
        SUPABASE_KEY = SUPABASE_KEY or secrets_data.get("SUPABASE_KEY", "")  # Fill from secrets.

# Initialize the Supabase client when credentials exist.
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None  # Client.
