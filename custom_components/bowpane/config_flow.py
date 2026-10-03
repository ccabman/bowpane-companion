"""Pair a TV and select its read-only scope using Home Assistant's own UI."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .pairing import validate_selection, validate_panel
from .entitlements import reported_pro, preserve_pro_settings

DOMAIN = "bowpane"


class BowPaneFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return BowPaneOptionsFlow()

    async def async_step_user(self, user_input=None):
        # HA's config-flow HTTP endpoints enforce administrator access. They do
        # not put a user_id into flow context. Do not invent that field.
        if self.context.get("source") != config_entries.SOURCE_USER:
            return self.async_abort(reason="admin_required")
        if DOMAIN not in self.hass.data:
            return await self.async_step_install()
        errors = {}
        if user_input is not None:
            cameras = [{"entity": user_input[f"camera_{i}"], "main": user_input.get(f"main_{i}", "")}
                       for i in range(1, 5) if user_input.get(f"camera_{i}")]
            sensors = user_input.get("sensors", [])
            try:
                validate_selection(cameras, sensors)
                entities = sensors + [r[k] for r in cameras for k in ("entity", "main") if r.get(k)]
                if any(self.hass.states.get(e) is None for e in entities):
                    raise ValueError("Missing entity")
                key_hash = self.hass.data[DOMAIN]["pairings"].claim(user_input["code"].replace(" ", ""), self.flow_id)
            except ValueError:
                errors["base"] = "invalid_pairing"
            else:
                return self.async_create_entry(title=user_input["name"], data={
                    "key_hash": key_hash, "confirmed": False, "cameras": cameras, "sensors": sensors})
        schema = {
            vol.Required("name", default="Living room TV"): str,
            vol.Required("code"): str,
        }
        for i in range(1, 5):
            key = vol.Required(f"camera_{i}") if i == 1 else vol.Optional(f"camera_{i}")
            schema[key] = selector.EntitySelector(selector.EntitySelectorConfig(domain="camera"))
            schema[vol.Optional(f"main_{i}")] = selector.EntitySelector(selector.EntitySelectorConfig(domain="camera"))
        schema[vol.Optional("sensors", default=[])] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor", "binary_sensor"], multiple=True))
        return self.async_show_form(step_id="user", data_schema=vol.Schema(schema), errors=errors)

    async def async_step_install(self, user_input=None):
        if self.context.get("source") != config_entries.SOURCE_USER:
            return self.async_abort(reason="admin_required")
        if user_input is not None:
            return self.async_create_entry(title="BowPane pairing service", data={"hub": True})
        return self.async_show_form(step_id="install", data_schema=vol.Schema({}))


class BowPaneOptionsFlow(config_entries.OptionsFlow):
    """Edit an existing TV's scope without replacing its pairing credential."""

    async def async_step_init(self, user_input=None):
        entry = self.config_entry
        if entry.data.get("hub"):
            return self.async_abort(reason="select_tv")
        pro = reported_pro(self.hass, entry)
        errors = {}
        if user_input is not None:
            opening = user_input.get("default_view", entry.data.get("default_view", "glance"))
            cameras = [{"entity": user_input[f"camera_{i}"], "main": user_input.get(f"main_{i}", "")}
                       for i in range(1, 5) if user_input.get(f"camera_{i}")]
            sensors = user_input.get("sensors", [])
            panel = {"title": user_input.get("panel_title", "Home Panel"),
                     "columns": int(user_input.get("panel_columns", 3)),
                     "show_clock": user_input.get("panel_clock", True),
                     "entities": [user_input[f"panel_{i}"] for i in range(1, 7) if user_input.get(f"panel_{i}")]}
            if not pro:
                cameras, panel = preserve_pro_settings(entry.data, cameras, panel)
            try:
                if opening not in ("glance", "grid", "panel"):
                    raise ValueError("Invalid opening screen")
                if opening == "panel" and not pro and opening != entry.data.get("default_view"):
                    raise ValueError("Home Panel requires Pro")
                validate_selection(cameras, sensors)
                validate_panel(panel)
                entities = sensors + (panel["entities"] if pro else []) + [r[k] for r in cameras for k in (("entity", "main") if pro else ("entity",)) if r.get(k)]
                if any(self.hass.states.get(e) is None for e in entities):
                    raise ValueError("Missing entity")
            except ValueError:
                errors["base"] = "invalid_selection"
            else:
                self.hass.config_entries.async_update_entry(entry, title=user_input["name"],
                    data={**entry.data, "cameras": cameras, "sensors": sensors, "panel": panel,
                          "default_view": opening,
                          "crop_to_fill": user_input.get("crop_to_fill", entry.data.get("crop_to_fill", False)),
                          "edge_to_edge": user_input.get("edge_to_edge", entry.data.get("edge_to_edge", False)),
                          "grid": {"showClock": user_input.get("grid_clock", True),
                                   "clockPosition": user_input.get("grid_clock_position", "top_right"),
                                   "clockBackground": user_input.get("grid_clock_background", True)}})
                return self.async_create_entry(title="", data={})
        suggested = {"name": entry.title, "sensors": entry.data.get("sensors", []),
                     "crop_to_fill": entry.data.get("crop_to_fill", False),
                     "default_view": entry.data.get("default_view", "glance"),
                     "edge_to_edge": entry.data.get("edge_to_edge", False)}
        panel = entry.data.get("panel", {})
        grid = entry.data.get("grid", {})
        suggested.update(grid_clock=grid.get("showClock", True),
                         grid_clock_position=grid.get("clockPosition", "top_right"),
                         grid_clock_background=grid.get("clockBackground", True))
        suggested.update(panel_title=panel.get("title", "Home Panel"), panel_columns=str(panel.get("columns", 3)), panel_clock=panel.get("show_clock", True))
        for i, entity in enumerate(panel.get("entities", []), 1):
            suggested[f"panel_{i}"] = entity
        for i, camera in enumerate(entry.data.get("cameras", []), 1):
            suggested[f"camera_{i}"] = camera["entity"]
            if camera.get("main"):
                suggested[f"main_{i}"] = camera["main"]
        if user_input is not None:
            suggested = user_input
        schema = {vol.Required("name"): str}
        opening_options = [{"value": "glance", "label": "Glance"}, {"value": "grid", "label": "Camera Grid"}]
        if pro or entry.data.get("default_view") == "panel":
            opening_options.append({"value": "panel", "label": "Home Panel · Pro (Glance when unavailable)"})
        schema[vol.Required("default_view")] = selector.SelectSelector(selector.SelectSelectorConfig(options=opening_options))
        schema[vol.Required("edge_to_edge", default=False)] = bool
        schema[vol.Required("crop_to_fill", default=False)] = bool
        schema[vol.Required("grid_clock", default=True)] = bool
        schema[vol.Required("grid_clock_position", default="top_right")] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=[
                {"value": key, "label": label} for key, label in [
                    ("top_left", "Top left"), ("top_center", "Top center"),
                    ("top_right", "Top right"), ("center", "Center"),
                    ("bottom_left", "Bottom left"), ("bottom_center", "Bottom center"),
                    ("bottom_right", "Bottom right")]]))
        schema[vol.Required("grid_clock_background", default=True)] = bool
        for i in range(1, 5):
            key = vol.Required(f"camera_{i}") if i == 1 else vol.Optional(f"camera_{i}")
            schema[key] = selector.EntitySelector(selector.EntitySelectorConfig(domain="camera"))
            if pro:
                schema[vol.Optional(f"main_{i}")] = selector.EntitySelector(selector.EntitySelectorConfig(domain="camera"))
        schema[vol.Optional("sensors")] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor", "binary_sensor"], multiple=True))
        if pro:
            schema[vol.Required("panel_title", default="Home Panel")] = vol.All(str, vol.Length(min=1, max=60))
            schema[vol.Required("panel_columns", default="3")] = vol.In(["2", "3"])
            schema[vol.Required("panel_clock", default=True)] = bool
            for i in range(1, 7):
                schema[vol.Optional(f"panel_{i}")] = selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor", "binary_sensor"]))
        return self.async_show_form(step_id="init", errors=errors,
            description_placeholders={"access_status": "TV reports Pro (not independently purchase-verified)" if pro else "Free or TV offline: saved Pro settings are retained. Open the TV app and reopen Configure to refresh."},
            data_schema=self.add_suggested_values_to_schema(vol.Schema(schema), suggested))
