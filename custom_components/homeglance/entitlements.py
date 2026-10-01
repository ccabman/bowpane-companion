"""Device-reported UI hints, NOT proof of an Apple purchase or authorization."""
import time

SOURCES = {"development_preview", "app_verified", "app_default"}

def validate_report(body):
    if not isinstance(body, dict) or set(body) != {"tier", "source"}:
        raise ValueError("Invalid report")
    if body["tier"] not in ("free", "pro") or body["source"] not in SOURCES:
        raise ValueError("Invalid report")
    return dict(body)

def reported_pro(hass, entry):
    report = hass.data["homeglance"].get("capabilities", {}).get(entry.data.get("key_hash"))
    return bool(report and time.monotonic() - report["received"] < 120 and report["tier"] == "pro")

def preserve_pro_settings(old, cameras, panel):
    """Keep hidden settings by camera identity, never transfer HQ feeds to a new camera."""
    mains = {row["entity"]: row.get("main", "") for row in old.get("cameras", [])}
    return ([{**row, "main": mains.get(row["entity"], "")} for row in cameras], old.get("panel", panel))
