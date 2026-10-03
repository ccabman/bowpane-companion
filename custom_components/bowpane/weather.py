"""Read only the explicitly selected current-weather and indoor-temperature data."""
import math


def validate_weather(config):
    if not isinstance(config, dict) or type(config.get("show", False)) is not bool:
        raise ValueError("Invalid weather settings")
    entity, indoor = config.get("entity", ""), config.get("indoor", "")
    if not isinstance(entity, str) or (entity and not entity.startswith("weather.")):
        raise ValueError("Select a weather entity")
    if config.get("show") and not entity:
        raise ValueError("Select a weather entity to show weather")
    if not isinstance(indoor, str) or (indoor and not indoor.startswith("sensor.")):
        raise ValueError("Select an indoor temperature sensor")


def number(value):
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def weather_snapshot(hass, config):
    validate_weather(config)
    if not config.get("show", False):
        return {"show": False}
    entity, indoor = config.get("entity", ""), config.get("indoor", "")
    outside = hass.states.get(entity)
    inside = hass.states.get(indoor) if indoor else None
    available = outside is not None and outside.state not in ("unknown", "unavailable")
    indoor_available = inside is not None and inside.state not in ("unknown", "unavailable")
    return {"show": True, "entity": entity,
            "condition": str(outside.state) if available else "unavailable",
            "temperature": number(outside.attributes.get("temperature")) if available else None,
            "unit": str(outside.attributes.get("temperature_unit", "")) if available else "",
            "indoorEntity": indoor or None,
            "indoorTemperature": number(inside.state) if indoor_available else None,
            "indoorUnit": str(inside.attributes.get("unit_of_measurement", "")) if indoor_available else ""}
