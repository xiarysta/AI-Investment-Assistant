import os
from dotenv import load_dotenv

load_dotenv()

WELLFLOW_API_KEY = os.getenv("WELLFLOW_API_KEY", "")
WELLFLOW_BASE_URL = "https://api.wellflow.dev/v1"
WELLFLOW_MODEL = "claude-haiku-4.5"
