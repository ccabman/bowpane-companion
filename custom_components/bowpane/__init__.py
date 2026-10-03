"""Read-only, entity-scoped BowPane companion."""
from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.camera import async_request_stream
from homeassistant.helpers import config_validation as cv
from .pairing import Pairings, digest
from .entitlements import validate_report
import time

DOMAIN = "bowpane"
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass, config):
    hass.data[DOMAIN] = {"pairings": Pairings(), "entries": {}}
    hass.http.register_view(CompanionView(hass))
    return True


async def async_setup_entry(hass, entry):
    hass.data[DOMAIN]["entries"][entry.entry_id] = entry
    return True


async def async_unload_entry(hass, entry):
    hass.data[DOMAIN]["entries"].pop(entry.entry_id, None)
    return True


def snapshot(hass, entry):
    cameras = []
    for row in entry.data["cameras"]:
        state = hass.states.get(row["entity"])
        cameras.append({**row, "name": state.name if state else row["entity"]})
    sensors = []
    for entity in entry.data["sensors"]:
        state = hass.states.get(entity)
        sensors.append({"id": entity, "name": state.name if state else entity,
                        "value": str(state.state) if state else "unavailable",
                        "unit": str(state.attributes.get("unit_of_measurement", "")) if state else ""})
    panel = entry.data.get("panel", {"title": "Home Panel", "columns": 3, "show_clock": True, "entities": []})
    tiles = []
    for entity in panel["entities"]:
        state = hass.states.get(entity)
        tiles.append({"id": entity, "name": state.name if state else entity,
                      "value": str(state.state) if state else "unavailable",
                      "unit": str(state.attributes.get("unit_of_measurement", "")) if state else ""})
    return {"name": entry.title, "cameras": cameras, "sensors": sensors,
            "defaultView": entry.data.get("default_view", "glance"),
            "cropToFill": entry.data.get("crop_to_fill", False),
            "edgeToEdge": entry.data.get("edge_to_edge", False),
            "grid": entry.data.get("grid", {"showClock": True, "clockPosition": "top_right", "clockBackground": True}),
            "panel": {"title": panel["title"], "columns": panel["columns"], "showClock": panel["show_clock"], "tiles": tiles}}


class CompanionView(HomeAssistantView):
    url = "/api/bowpane/{action}"
    name = "api:bowpane"
    # These routes use a separate 256-bit, entity-scoped capability, NOT HA auth.
    requires_auth = False

    def __init__(self, hass):
        self.hass = hass

    async def post(self, request, action):
        # Native app only; no browser CORS or URL credentials. Reverse proxy must
        # preserve HTTPS scheme through HA's trusted-proxy configuration.
        if not request.secure or request.headers.get("Origin"):
            return web.json_response({"error": "https_required"}, status=403)
        runtime = self.hass.data[DOMAIN]
        broker = runtime["pairings"]
        headers = {"Cache-Control": "no-store"}
        if action == "start":
            try:
                return web.json_response(broker.start(), headers=headers)
            except ValueError:
                return web.json_response({"error": "rate_limited"}, status=429, headers=headers)
        secret = request.headers.get("X-BowPane-Key", "")
        if not 40 <= len(secret) <= 64:
            return web.json_response({"error": "unauthorized"}, status=401, headers=headers)
        pending = broker.get(secret)
        entries = runtime["entries"].values()
        entry = next((e for e in entries if e.data.get("key_hash") == digest(secret)), None)
        if action == "cancel":
            broker.cancel(secret)
            return web.json_response({"ok": True}, headers=headers)
        if action == "status":
            if pending is None:
                return web.json_response({"error": "expired"}, status=410, headers=headers)
            return web.json_response({"status": "approved" if entry else "waiting",
                                      "configuration": snapshot(self.hass, entry) if entry else None}, headers=headers)
        if action == "confirm":
            if entry is not None and entry.data.get("confirmed"):
                return web.json_response(snapshot(self.hass, entry), headers=headers)
            if pending is None or entry is None:
                return web.json_response({"error": "expired"}, status=410, headers=headers)
            self.hass.config_entries.async_update_entry(entry, data={**entry.data, "confirmed": True})
            broker.cancel(secret)
            return web.json_response(snapshot(self.hass, entry), headers=headers)
        if entry is None or not entry.data.get("confirmed"):
            return web.json_response({"error": "unauthorized"}, status=401, headers=headers)
        if action == "capabilities":
            if request.content_length is None or request.content_length > 512:
                return web.json_response({"error": "invalid_request"}, status=400, headers=headers)
            try:
                report = validate_report(await request.json())
            except (ValueError, TypeError):
                return web.json_response({"error": "invalid_report"}, status=400, headers=headers)
            # Ephemeral per-device UI hints; no purchase proof, no disk writes per heartbeat.
            runtime.setdefault("capabilities", {})[entry.data["key_hash"]] = {**report, "received": time.monotonic()}
            return web.json_response({"ok": True}, headers=headers)
        if action == "configuration":
            return web.json_response(snapshot(self.hass, entry), headers=headers)
        if action == "stream":
            if request.content_length is None or request.content_length > 1024:
                return web.json_response({"error": "invalid_request"}, status=400, headers=headers)
            try:
                body = await request.json()
                entity = body.get("entity")
                allowed = {r[k] for r in entry.data["cameras"] for k in ("entity", "main") if r.get(k)}
                if not isinstance(entity, str) or entity not in allowed:
                    return web.json_response({"error": "forbidden"}, status=403, headers=headers)
                url = await async_request_stream(self.hass, entity, fmt="hls")
                return web.json_response({"url": url}, headers=headers)
            except Exception:
                # Never log stream URLs, credentials, or camera exceptions.
                return web.json_response({"error": "stream_unavailable"}, status=503, headers=headers)
        return web.json_response({"error": "not_found"}, status=404, headers=headers)
