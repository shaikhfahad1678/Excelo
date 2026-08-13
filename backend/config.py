import os
import sys
from pathlib import Path

# Add project root directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
# Load .env file from project root
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# Cloudflare R2 configurations
CLOUDFLARE_R2_ACCOUNT_ID = os.getenv("CLOUDFLARE_R2_ACCOUNT_ID") or os.getenv("R2_ACCOUNT_ID")
CLOUDFLARE_R2_ACCESS_KEY_ID = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID") or os.getenv("R2_ACCESS_KEY_ID")
CLOUDFLARE_R2_SECRET_ACCESS_KEY = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY") or os.getenv("R2_SECRET_ACCESS_KEY")
CLOUDFLARE_R2_BUCKET_NAME = os.getenv("CLOUDFLARE_R2_BUCKET_NAME") or os.getenv("R2_BUCKET_NAME")



# Target columns for standard bank statement export
REQUIRED_COLUMNS = [
    "Date",
    "Description",
    "Cheque No.",
    "Ref No.",
    "Debit",
    "Credit",
    "Balance",
    "Currency"
]

# Supported date patterns for parsing & normalization
DATE_PATTERNS = [
    r"\b\d{2}[/-]\d{2}[/-]\d{4}\b",
    r"\b\d{2}[/-]\d{2}[/-]\d{2}\b",
    r"\b\d{4}[/-]\d{2}[/-]\d{2}\b",
    r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b",
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}\b",
]

# Configurable defaults
DEFAULT_EXCEL_FILENAME = "BankStatement_{date}.xlsx"
