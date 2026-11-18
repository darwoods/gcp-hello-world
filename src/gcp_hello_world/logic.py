from datetime import datetime, timezone

def generate_greeting(name: str = "World") -> dict:
    clean_name = name.strip() or "World"
    now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    return {
        "message": f"Hello, {clean_name} from Cloud Run!",
        "timestamp": now,
    }