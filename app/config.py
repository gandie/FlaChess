from pathlib import Path

from dotenv import load_dotenv

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def load_environment() -> None:
    load_dotenv(_ENV_FILE, override=False)
