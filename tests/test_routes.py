"""Adapter unit tests with minimal HA/aiohttp doubles, not a live HA test."""
import asyncio
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest

def module(name, **values):
    result = ModuleType(name)
    result.__dict__.update(values)
    sys.modules[name] = result
    return result

module("aiohttp", web=SimpleNamespace(json_response=lambda data, status=200, headers=None: SimpleNamespace(data=data, status=status)))
module("homeassistant")
module("homeassistant.components")
module("homeassistant.helpers", config_validation=SimpleNamespace(config_entry_only_config_schema=lambda domain: domain))
module("homeassistant.components.http", HomeAssistantView=object)
async def stream(hass, camera, fmt): return "/api/hls/test/master.m3u8"
module("homeassistant.components.camera", async_request_stream=stream)
path = Path(__file__).parents[1] / "custom_components/bowpane"
spec = importlib.util.spec_from_file_location("route_fixture", path / "__init__.py", submodule_search_locations=[str(path)])
integration = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = integration
spec.loader.exec_module(integration)

class Request:
    secure = True
    content_length = 32
    def __init__(self, secret="", body=None):
        self.headers = {"X-BowPane-Key": secret}
        self.body = body or {}
    async def json(self): return self.body

class RouteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.broker = integration.Pairings()
        self.entries = {}
        self.hass = SimpleNamespace(data={"bowpane":{"pairings": self.broker, "entries":self.entries}},
            states=SimpleNamespace(get=lambda entity: None),
            config_entries=SimpleNamespace(async_update_entry=lambda entry, data: setattr(entry, "data", data)))
        self.view = integration.CompanionView(self.hass)
        self.started = self.broker.start()
        self.secret = self.started["secret"]

    def approve_in_ha(self):
        hashed = self.broker.claim(self.started["code"], "flow")
        self.entry = SimpleNamespace(title="TV", data={"key_hash":hashed,"confirmed":False,
            "cameras":[{"entity":"camera.door","main":"camera.main"}],"sensors":["sensor.temp"]})
        self.entries["tv"] = self.entry

    async def test_both_approvals_required(self):
        request = Request(self.secret)
        self.assertEqual((await self.view.post(request, "configuration")).status, 401)
        self.approve_in_ha()
        self.assertEqual((await self.view.post(request, "status")).data["status"], "approved")
        self.assertEqual((await self.view.post(request, "configuration")).status, 401)
        self.assertEqual((await self.view.post(request, "confirm")).status, 200)
        self.assertEqual((await self.view.post(request, "configuration")).status, 200)
        self.assertEqual((await self.view.post(request, "confirm")).status, 200)  # retry safe

    async def test_screen_margin_setting_defaults_and_updates(self):
        self.approve_in_ha()
        await self.view.post(Request(self.secret), "confirm")
        self.assertFalse((await self.view.post(Request(self.secret), "configuration")).data["edgeToEdge"])
        self.entry.data["edge_to_edge"] = True
        self.assertTrue((await self.view.post(Request(self.secret), "configuration")).data["edgeToEdge"])
        self.entry.data["edge_to_edge"] = False
        self.assertFalse((await self.view.post(Request(self.secret), "configuration")).data["edgeToEdge"])

    async def test_grid_clock_defaults_and_updates(self):
        self.approve_in_ha()
        await self.view.post(Request(self.secret), "confirm")
        configuration = (await self.view.post(Request(self.secret), "configuration")).data
        self.assertEqual(configuration["grid"], {"showClock": True, "clockPosition": "top_right", "clockBackground": True})
        for position in ["top_left", "top_center", "top_right", "center", "bottom_left", "bottom_center", "bottom_right"]:
            self.entry.data["grid"] = {"showClock": False, "clockPosition": position, "clockBackground": False}
            self.assertEqual((await self.view.post(Request(self.secret), "configuration")).data["grid"], self.entry.data["grid"])

    async def test_scope_and_revocation(self):
        self.approve_in_ha()
        await self.view.post(Request(self.secret), "confirm")
        self.assertEqual((await self.view.post(Request(self.secret, {"entity":"camera.door"}), "stream")).status, 200)
        self.assertEqual((await self.view.post(Request(self.secret, {"entity":"camera.private"}), "stream")).status, 403)
        self.entries.clear()
        self.assertEqual((await self.view.post(Request(self.secret), "configuration")).status, 401)

    async def test_no_secret_or_code_cannot_read(self):
        self.approve_in_ha()
        for secret in ["", self.started["code"], "x" * 43]:
            self.assertEqual((await self.view.post(Request(secret), "configuration")).status, 401)

    async def test_cancel_blocks_confirmation(self):
        self.approve_in_ha()
        await self.view.post(Request(self.secret), "cancel")
        self.assertEqual((await self.view.post(Request(self.secret), "confirm")).status, 410)
        self.assertEqual((await self.view.post(Request(self.secret), "configuration")).status, 401)

    async def test_plaintext_and_browser_requests_rejected(self):
        request = Request(self.secret); request.secure = False
        self.assertEqual((await self.view.post(request, "start")).status, 403)
        request.secure = True; request.headers["Origin"] = "https://other.example"
        self.assertEqual((await self.view.post(request, "start")).status, 403)

    async def test_capability_reports_need_confirmed_pairing(self):
        request = Request(self.secret, {"tier": "pro", "source": "development_preview"})
        self.assertEqual((await self.view.post(request, "capabilities")).status, 401)
        self.approve_in_ha()
        self.assertEqual((await self.view.post(request, "capabilities")).status, 401)
        await self.view.post(Request(self.secret), "confirm")
        self.assertEqual((await self.view.post(request, "capabilities")).status, 200)
        from route_fixture.entitlements import reported_pro, preserve_pro_settings
        self.assertTrue(reported_pro(self.hass, self.entry))
        other = SimpleNamespace(data={"key_hash": "other"})
        self.assertFalse(reported_pro(self.hass, other))
        report = self.hass.data["bowpane"]["capabilities"][self.entry.data["key_hash"]]
        report["received"] -= 121
        self.assertFalse(reported_pro(self.hass, self.entry))
        cameras, panel = preserve_pro_settings({"cameras": [{"entity": "camera.door", "main": "camera.hq"}], "panel": {"title": "Saved"}},
                                              [{"entity": "camera.door", "main": ""}, {"entity": "camera.new", "main": "camera.hq"}], {})
        self.assertEqual(cameras[0]["main"], "camera.hq")
        self.assertEqual(cameras[1]["main"], "")
        self.assertEqual(panel, {"title": "Saved"})
        self.assertEqual((await self.view.post(Request(self.secret, {"tier": "free", "source": "development_preview"}), "capabilities")).status, 200)
        self.assertFalse(reported_pro(self.hass, self.entry))
        self.assertEqual((await self.view.post(Request(self.secret, {"tier": "bogus", "source": "development_preview"}), "capabilities")).status, 400)
        self.entries.clear()
        self.assertEqual((await self.view.post(request, "capabilities")).status, 401)

if __name__ == "__main__": unittest.main()
