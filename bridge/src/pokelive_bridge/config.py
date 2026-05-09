import os
from pathlib import Path

from dotenv import load_dotenv

# Walk up from this file to find .env, regardless of CWD when server starts
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path, override=True)

OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
OPENAI_CHAT_MODEL: str = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o")
OPENAI_MAX_COMPLETION_TOKENS: int = int(
    os.environ.get("OPENAI_MAX_COMPLETION_TOKENS", "4096")
)
