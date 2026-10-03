import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location("weather_policy", Path(__file__).parents[1] / "custom_components/bowpane/weather.py")
weather = importlib.util.module_from_spec(spec)
spec.loader.exec_module(weather)


class WeatherTests(unittest.TestCase):
    def test_disabled_weather_does_not_read_entities(self):
        def forbidden(_): raise AssertionError("Disabled weather must not read entities")
        hass = SimpleNamespace(states=SimpleNamespace(get=forbidden))
        self.assertEqual(weather.weather_snapshot(hass, {"show": False}), {"show": False})

    def test_only_selected_entities_are_read(self):
        queried = []
        rows = {"weather.home": SimpleNamespace(state="sunny", attributes={"temperature": 0, "temperature_unit": "°C", "latitude": 99}),
                "sensor.inside": SimpleNamespace(state="72.5", attributes={"unit_of_measurement": "°F"})}
        def get(entity):
            queried.append(entity)
            return rows.get(entity)
        hass = SimpleNamespace(states=SimpleNamespace(get=get))
        result = weather.weather_snapshot(hass, {"show": True, "entity": "weather.home", "indoor": "sensor.inside"})
        self.assertEqual(queried, ["weather.home", "sensor.inside"])
        self.assertEqual(result["temperature"], 0)
        self.assertEqual(result["unit"], "°C")
        self.assertEqual(result["indoorTemperature"], 72.5)
        self.assertEqual(result["indoorUnit"], "°F")
        self.assertNotIn("latitude", result)

    def test_missing_unknown_and_nonfinite_values(self):
        hass = SimpleNamespace(states=SimpleNamespace(get=lambda _: None))
        result = weather.weather_snapshot(hass, {"show": True, "entity": "weather.home"})
        self.assertEqual(result["condition"], "unavailable")
        self.assertIsNone(result["temperature"])
        for value in ["unknown", "unavailable", "nan", "inf", None, True]:
            self.assertIsNone(weather.number(value))

    def test_rejects_out_of_scope_entities(self):
        for config in [{"show": True}, {"show": True, "entity": "switch.test"},
                       {"show": True, "entity": "weather.test", "indoor": "camera.test"}]:
            with self.assertRaises(ValueError): weather.validate_weather(config)
