from pipeline.quality import validate_event_record


def validate_watch_event(event: dict) -> bool:
    try:
        validate_event_record("watch", event)
        return True
    except Exception:
        return False


def validate_rate_event(event: dict) -> bool:
    try:
        validate_event_record("rate", event)
        return True
    except Exception:
        return False
