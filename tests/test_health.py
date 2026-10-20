"""Module health failures are independent and output is strictly redacted."""
import asyncio
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('health_policy', Path(__file__).parents[1] / 'custom_components/bowpane/health.py')
health = importlib.util.module_from_spec(spec)
spec.loader.exec_module(health)

class HealthTests(unittest.IsolatedAsyncioTestCase):
    async def test_failed_module_cannot_block_others_or_leak_details(self):
        async def broken(): raise ValueError('PRIVATE_SENTINEL')
        async def waiting(): return {'state':'waiting_for_mac', 'reason':'waiting_for_mac', 'secret':'PRIVATE_SENTINEL'}
        result = await health.health({'photos': broken, 'calendars': waiting})
        self.assertEqual(result['modules']['photos']['state'], 'error')
        self.assertEqual(result['modules']['calendars']['state'], 'waiting_for_mac')
        self.assertEqual(result['modules']['music']['state'], 'unsupported')
        self.assertNotIn('PRIVATE_SENTINEL', repr(result))

    async def test_invalid_adapter_results_fail_closed(self):
        for value in [[], None, {'state':[], 'reason':'adapter_error'}, {'state':'healthy','reason':'PRIVATE_SENTINEL'}]:
            async def invalid(value=value): return value
            self.assertEqual((await health.module_health(invalid))['state'], 'error')
        self.assertEqual((await health.module_health(dict))['state'], 'error')

    async def test_timeout_is_redacted(self):
        async def timeout(): raise TimeoutError('PRIVATE_SENTINEL')
        self.assertEqual(await health.module_health(timeout), health.record('error','adapter_timeout'))

    async def test_hung_module_times_out_while_other_module_finishes(self):
        async def hung():
            await asyncio.Event().wait()
        async def responsive():
            return {"state": "stale", "reason": "no_successful_sync"}
        result = await health.health({"photos": hung, "calendars": responsive})
        self.assertEqual(result["modules"]["photos"]["reason"], "adapter_timeout")
        self.assertEqual(result["modules"]["calendars"]["state"], "stale")
