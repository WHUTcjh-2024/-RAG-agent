"""Backend application package."""
from pathlib import Path

from dotenv import load_dotenv


# Local development configuration. Existing process variables take precedence.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
