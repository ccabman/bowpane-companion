"""Versioned authorization policy; entitlement hints never grant capabilities."""
ROLES = {"tv_display": ("configuration.read", "camera.stream"),
         "mac_agent": ("health.read",)}


def negotiate(body):
    if not isinstance(body, dict) or set(body) != {"versions", "role"}:
        raise ValueError("Invalid negotiation")
    versions = body["versions"]
    if not isinstance(versions, list) or not 1 <= len(versions) <= 8 or any(type(v) is not int for v in versions):
        raise ValueError("Invalid versions")
    if 2 not in versions or not isinstance(body["role"], str) or body["role"] not in ROLES:
        raise ValueError("Unsupported protocol or role")
    return {"protocol_version": 2, "role": body["role"],
            "capabilities": list(ROLES[body["role"]])}


def grants(data, capability):
    # Old entries retain exactly their existing native TV privileges.
    if "protocol_version" not in data:
        return "role" not in data and "capabilities" not in data and capability in ROLES["tv_display"]
    return (type(data.get("protocol_version")) is int and data["protocol_version"] == 2
            and isinstance(data.get("role"), str)
            and isinstance(data.get("capabilities"), list)
            and capability in ROLES.get(data.get("role"), ())
            and capability in data.get("capabilities", []))


def describe(data):
    return {"protocolVersion": data.get("protocol_version", 1),
            "role": data.get("role", "tv_display"),
            "capabilities": [cap for cap in ("configuration.read", "camera.stream", "health.read") if grants(data, cap)]}
