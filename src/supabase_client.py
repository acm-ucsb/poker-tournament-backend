import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_DATABASE_URL: str = os.getenv("DATABASE_URL") or ""
SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY") or ""

if SUPABASE_DATABASE_URL == "" or SUPABASE_SECRET_KEY == "":
    raise ValueError(
        "SUPABASE_DATABASE_URL and SUPABASE_SECRET_KEY environment variables must be set."
    )

db_client: Client = create_client(SUPABASE_DATABASE_URL, SUPABASE_SECRET_KEY)
# modules get cached so this db_client can be reused across the application
