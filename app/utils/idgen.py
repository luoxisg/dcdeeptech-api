"""Utility: ID and API key generation."""
import secrets
import string
import uuid


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


def generate_api_key() -> str:
    """
    Generate a random API key with the dcdt_sk_live_ prefix.
    Returns the full plaintext key — store only the prefix + hash.
    """
    alphabet = string.ascii_letters + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(48))
    return f"dcdt_sk_live_{random_part}"


def extract_key_prefix(key: str) -> str:
    """Return the first 20 characters as the displayable prefix."""
    return key[:20]
