from datetime import datetime, timezone


def current_timestamp() -> int:
    """Return current UTC timestamp in seconds"""
    return int(datetime.now(timezone.utc).timestamp())
