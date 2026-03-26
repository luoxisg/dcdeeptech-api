"""Utility: mask sensitive strings for display / logging."""


def mask_api_key(key: str) -> str:
    """Show prefix + last 4 chars, mask the middle."""
    if len(key) <= 24:
        return key[:8] + "..." + key[-4:]
    return key[:20] + "..." + key[-4:]


def mask_email(email: str) -> str:
    """Show first 2 chars of local part, hide the rest."""
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        return f"{local}***@{domain}"
    return f"{local[:2]}{'*' * (len(local) - 2)}@{domain}"
