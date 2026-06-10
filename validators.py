# utils/validators.py
# Helper functions that check whether input is valid
# before we try to process it.

import re
from urllib.parse import urlparse

SUPPORTED_DOMAINS = [
    "youtube.com", "youtu.be",
    "tiktok.com",
    "instagram.com",
]

def is_valid_url(url: str) -> bool:
    """Check if a string is a valid HTTP/HTTPS URL."""
    try:
        result = urlparse(url)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False

def is_supported_platform(url: str) -> bool:
    """Check if the URL is from a platform we support."""
    try:
        netloc = urlparse(url).netloc.lower()
        # strip www.
        netloc = netloc.replace("www.", "")
        return any(domain in netloc for domain in SUPPORTED_DOMAINS)
    except Exception:
        return False

def get_platform(url: str) -> str:
    """Return which platform a URL belongs to."""
    netloc = urlparse(url).netloc.lower().replace("www.", "")
    if "youtube.com" in netloc or "youtu.be" in netloc:
        return "youtube"
    if "tiktok.com" in netloc:
        return "tiktok"
    if "instagram.com" in netloc:
        return "instagram"
    return "unknown"

def sanitize_filename(name: str) -> str:
    """Remove characters that are unsafe in filenames."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.strip().replace(" ", "_")
    return name[:80]  # cap length
