"""Two-process HA persistence lab. Invoked by test_process_restart.py only."""
import asyncio
import json
import logging
import os
import ssl
import sys
from pathlib import Path

import aiohttp
from homeassistant import loader
from homeassistant.bootstrap import async_from_config_dict
from homeassistant.core import HomeAssistant


async def main():
    mode, directory = sys.argv[1:]
    root = Path(directory).resolve()
    logging.disable(logging.CRITICAL)
    hass = HomeAssistant(str(root))
    loader.async_setup(hass)
    hass.config.skip_pip = True
    config = {'homeassistant': {'name': 'Synthetic restart lab', 'latitude':0, 'longitude':0,
        'elevation':0, 'unit_system':'metric', 'time_zone':'UTC', 'country':'US', 'currency':'USD'},
        'http': {'server_host':'127.0.0.1', 'server_port':18124,
                 'ssl_certificate':str(root/'localhost.pem'), 'ssl_key':str(root/'localhost.key')},
        'config':{}, 'api':{}}
    assert await async_from_config_dict(config, hass) is not None, 'HA bootstrap failed'
    await hass.async_start()
    # Never send a request unless this process owns the loopback TLS listener.
    server = getattr(hass.http, "_server", None)
    assert server is not None and server.is_serving(), "Lab listener did not start"
    assert server.sockets and all(sock.getsockname()[:2] == ("127.0.0.1", 18124) for sock in server.sockets), "Unexpected lab binding"
    context = ssl.create_default_context(cafile=str(root/'localhost.pem'))
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=context)) as client:
        async def request(action, secret='', body=None):
            async with client.post('https://127.0.0.1:18124/api/bowpane/'+action,
                headers={'X-BowPane-Key':secret}, json={} if body is None else body) as response:
                return response.status, await response.json()
        if mode == 'seed':
            flow = await hass.config_entries.flow.async_init('bowpane', context={'source':'user'})
            result = await hass.config_entries.flow.async_configure(flow['flow_id'], {})
            assert result['type'] == 'create_entry', 'Hub approval failed'
            await hass.async_block_till_done()
            async def pair(confirm):
                hass.data['bowpane']['pairings'].last_start = -float('inf')
                status, started = await request('v2_start', body={'versions':[2], 'role':'mac_agent'})
                assert status == 200, 'Negotiation failed'
                flow = await hass.config_entries.flow.async_init('bowpane', context={'source':'user'})
                result = await hass.config_entries.flow.async_configure(flow['flow_id'],
                    {'name':'Synthetic agent', 'code':started['code'], 'role':'mac_agent'})
                assert result['type'] == 'create_entry', 'Device approval failed'
                await hass.async_block_till_done()
                if confirm:
                    assert (await request('confirm', started['secret']))[0] == 200, 'Confirmation failed'
                return started['secret'], result['result'].entry_id
            confirmed, confirmed_id = await pair(True)
            pending, pending_id = await pair(False)
            private = root/'test-credentials.json'
            private.write_text(json.dumps({'confirmed':confirmed,'pending':pending,
                'confirmed_id':confirmed_id, 'pending_id':pending_id}))
            os.chmod(private, 0o600)
        else:
            saved = json.loads((root/'test-credentials.json').read_text())
            assert (await request('v2_health', saved['confirmed']))[0] == 200, 'Confirmed pairing did not survive restart'
            assert (await request('confirm', saved['confirmed']))[0] == 200, 'Confirm retry failed'
            assert (await request('v2_health', saved['pending']))[0] == 401, 'Unconfirmed pairing gained access'
            assert (await request('confirm', saved['pending']))[0] == 410, 'Pending claim survived restart'
            await hass.config_entries.async_remove(saved['confirmed_id'])
            assert (await request('v2_health', saved['confirmed']))[0] == 401, 'Revocation failed'
    await hass.async_stop(force=True)
    print(mode+' process passed')

if __name__ == '__main__':
    asyncio.run(main())
