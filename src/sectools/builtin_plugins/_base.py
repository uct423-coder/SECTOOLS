"""Plugin validation and API versioning."""

PLUGIN_API_VERSION = "1.0"

REQUIRED_ATTRS = ("PLUGIN_NAME", "run")


def validate_plugin(module) -> tuple[bool, str]:
    """Validate a plugin module has required attributes.

    Returns (is_valid, error_message).
    """
    for attr in REQUIRED_ATTRS:
        if not hasattr(module, attr):
            return False, f"Missing required attribute: {attr}"
    if not callable(getattr(module, "run", None)):
        return False, "'run' must be callable"
    return True, ""
