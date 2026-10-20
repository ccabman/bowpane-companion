"""Configuration adapter tests; HA UI/runtime remains a release gate."""
import importlib
from types import SimpleNamespace
import unittest
from test_routes import integration, module

class Flow:
    def __init_subclass__(cls, **kwargs): pass
    def async_create_entry(self, **kwargs): return {'type': 'create_entry', **kwargs}
    def async_abort(self, **kwargs): return {'type': 'abort', **kwargs}

module('voluptuous')
module('homeassistant.config_entries', ConfigFlow=Flow, OptionsFlow=Flow, SOURCE_USER='user')
module('homeassistant.core', callback=lambda f: f)
module('homeassistant.helpers.selector')
flow_module = importlib.import_module('route_fixture.config_flow')

class ConfigFlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_agent_approval_uses_pending_policy_without_cameras(self):
        broker = integration.Pairings()
        from route_fixture.protocol import negotiate
        policy = negotiate({'versions': [2], 'role': 'mac_agent'})
        started = broker.start(policy)
        flow = flow_module.BowPaneFlow()
        flow.context = {'source': 'user'}
        flow.flow_id = 'test-flow'
        flow.hass = SimpleNamespace(data={'bowpane': {'pairings': broker}})
        result = await flow.async_step_user({'name': 'Synthetic Mac', 'code': started['code'], 'role': 'mac_agent'})
        self.assertEqual(result['type'], 'create_entry')
        self.assertEqual(result['data']['capabilities'], ['health.read'])
        self.assertNotIn('cameras', result['data'])
        self.assertFalse(result['data']['confirmed'])
        options = flow_module.BowPaneOptionsFlow()
        options.config_entry = SimpleNamespace(data=result['data'])
        self.assertEqual((await options.async_step_init())['reason'], 'agent_scope_fixed')
