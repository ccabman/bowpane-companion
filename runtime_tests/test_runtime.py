"""Uses real HA config entries, schemas, HTTP middleware and device routes."""
import gzip
from unittest.mock import patch

import pytest
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

pytestmark = pytest.mark.asyncio

async def setup(hass, hass_client):
    assert await async_setup_component(hass, 'http', {'http': {
        'server_host': '127.0.0.1', 'server_port': 18123,
        'use_x_forwarded_for': True, 'trusted_proxies': ['127.0.0.1']}})
    # Set up the real dependency graph; no household integrations or discovery.
    hub = MockConfigEntry(domain='bowpane', title='Synthetic pairing hub', data={'hub': True})
    hub.add_to_hass(hass)
    assert await hass.config_entries.async_setup(hub.entry_id)
    assert await async_setup_component(hass, "config", {})
    await hass.async_block_till_done()
    return await hass_client()

async def start(hass, client, role='mac_agent'):
    hass.data['bowpane']['pairings'].last_start = -float('inf')
    body = {'versions': [2], 'role': role}
    response = await client.post('/api/bowpane/v2_start', json=body, headers={'X-Forwarded-For':'127.0.0.1', 'X-Forwarded-Proto':'https'})
    assert response.status == 200
    return await response.json()

async def post(client, action, secret, body=None, **kwargs):
    return await client.post('/api/bowpane/' + action,
        json={} if body is None else body,
        headers={'X-Forwarded-For':'127.0.0.1', 'X-Forwarded-Proto': 'https', 'X-BowPane-Key': secret}, **kwargs)

async def approve(hass, started, role='mac_agent'):
    result = await hass.config_entries.flow.async_init('bowpane', context={'source': 'user'})
    assert result['type'] is FlowResultType.FORM
    data = {'name': 'Synthetic device', 'code': started['code'], 'role': role}
    if role == 'tv_display':
        hass.states.async_set('camera.synthetic', 'idle')
        hass.states.async_set('sensor.synthetic', '21')
        data.update(camera_1='camera.synthetic', sensors=['sensor.synthetic'])
    # Validate the actual HA selector schema, not a double.
    result['data_schema'](data)
    result = await hass.config_entries.flow.async_configure(result['flow_id'], data)
    assert result['type'] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    return result['result']

async def test_mac_real_flow_scope_restart_and_revocation(hass, hass_client):
    client = await setup(hass, hass_client)
    started = await start(hass, client)
    entry = await approve(hass, started)
    secret = started['secret']
    assert (await post(client, 'v2_health', secret)).status == 401
    response = await post(client, 'confirm', secret)
    assert response.status == 200
    assert (await response.json())['capabilities'] == ['health.read']
    for action in ['stream', 'configuration', 'capabilities']:
        assert (await post(client, action, secret)).status == 403
    response = await post(client, 'v2_health', secret)
    assert response.status == 200
    assert response.headers['Cache-Control'] == 'no-store'
    assert set((await response.json())['modules']) == {'photos','calendars','music'}
    assert await hass.config_entries.async_reload(entry.entry_id)
    assert (await post(client, 'v2_health', secret)).status == 200
    assert await hass.config_entries.async_remove(entry.entry_id)
    assert (await post(client, 'v2_health', secret)).status == 401

async def test_legacy_real_flow_and_stream_scope(hass, hass_client):
    client = await setup(hass, hass_client)
    response = await client.post('/api/bowpane/start', json={}, headers={'X-Forwarded-For':'127.0.0.1', 'X-Forwarded-Proto':'https'})
    assert response.status == 200
    started = await response.json()
    assert set(started) == {'secret','code','expiresIn'}
    entry = await approve(hass, started, 'tv_display')
    assert 'protocol_version' not in entry.data
    secret = started['secret']
    assert (await post(client, 'configuration', secret)).status == 401
    response = await post(client, 'status', secret)
    assert (await response.json())['configuration']['sensors'][0]['value'] == '21'
    assert (await post(client, 'confirm', secret)).status == 200
    response = await post(client, 'configuration', secret)
    data = await response.json()
    assert data['cameras'][0]['entity'] == 'camera.synthetic'
    assert 'protocolVersion' not in data
    with patch('custom_components.bowpane.async_request_stream', return_value='/api/hls/synthetic/master.m3u8') as stream:
        assert (await post(client, 'stream', secret, {'entity':'camera.unselected'})).status == 403
        stream.assert_not_called()
        assert (await post(client, 'stream', secret, {'entity':'camera.synthetic'})).status == 200
        stream.assert_awaited_once()
    assert (await post(client, 'v2_health', secret)).status == 403
    assert await hass.config_entries.async_remove(entry.entry_id)
    assert (await post(client, 'configuration', secret)).status == 401

async def test_real_http_boundaries(hass, hass_client):
    client = await setup(hass, hass_client)
    for headers in [{}, {'X-Forwarded-For':'127.0.0.1', 'X-Forwarded-Proto':'https','Origin':'https://example.invalid'}, {'X-Forwarded-For':'127.0.0.1', 'X-Forwarded-Proto':'https','Origin':''}]:
        response = await client.post('/api/bowpane/start', json={}, headers=headers)
        assert response.status == 403
        assert response.headers['Cache-Control'] == 'no-store'
    for body in [b'[]', b'{', b'null', b'"bad"', b'x'*513]:
        response = await client.post('/api/bowpane/v2_start', data=body, headers={'X-Forwarded-For':'127.0.0.1', 'X-Forwarded-Proto':'https'})
        assert response.status == 400
    # Content-Length is compressed size. The decompressed limit must still apply.
    response = await client.post('/api/bowpane/v2_start', data=gzip.compress(b' '*10000+b'{}'),
        headers={'X-Forwarded-For':'127.0.0.1', 'X-Forwarded-Proto':'https','Content-Encoding':'gzip'})
    assert response.status == 400

async def test_role_mismatch_and_lookup_lockout(hass, hass_client):
    client = await setup(hass, hass_client)
    started = await start(hass, client)
    flow = await hass.config_entries.flow.async_init('bowpane', context={'source':'user'})
    result = await hass.config_entries.flow.async_configure(flow['flow_id'],
        {'name':'Mismatch', 'code':started['code'], 'role':'tv_display'})
    assert result['type'] is FlowResultType.FORM
    assert result['errors'] == {'base': 'invalid_pairing'}
    broker = hass.data['bowpane']['pairings']
    for _ in range(5):
        with pytest.raises(ValueError): broker.policy_for_code('invalid')
    with pytest.raises(ValueError): broker.policy_for_code(started['code'])
    assert not any(e.data.get('role') == 'mac_agent' for e in hass.config_entries.async_entries('bowpane'))

async def test_admin_http_approval_boundary(hass, hass_client):
    client = await setup(hass, hass_client)
    from homeassistant.auth.const import GROUP_ID_READ_ONLY
    reader = await hass.auth.async_create_user('Synthetic read-only user', group_ids=[GROUP_ID_READ_ONLY])
    refresh = await hass.auth.async_create_refresh_token(reader, client_id="http://localhost/")
    token = hass.auth.async_create_access_token(refresh)
    assert hass.auth.async_validate_access_token(token) is not None
    response = await client.post('/api/config/config_entries/flow', json={'handler':'bowpane'},
        headers={'Authorization':'Bearer '+token})
    assert response.status == 401  # HA maps its Unauthorized admin exception to 401.
    response = await client.post('/api/config/config_entries/flow', json={'handler':'bowpane'},
        headers={'Authorization':''})
    assert response.status == 401
    response = await client.post('/api/config/config_entries/flow', json={'handler':'bowpane'})
    assert response.status == 200
    assert (await response.json())['type'] == 'form'

async def test_expiry_cancel_and_pending_loss(hass, hass_client):
    client = await setup(hass, hass_client)
    for mode in ['expiry','cancel','pending_loss']:
        started = await start(hass, client)
        entry = await approve(hass, started)
        broker = hass.data['bowpane']['pairings']
        if mode == 'expiry':
            broker.get(started['secret'])['expires'] = broker.clock()-1
        elif mode == 'cancel':
            assert (await post(client, 'cancel', started['secret'])).status == 200
        else:
            # A full process restart forgets all unconfirmed claims.
            broker.pending.clear()
        assert (await post(client, 'confirm', started['secret'])).status == 410
        assert (await post(client, 'v2_health', started['secret'])).status == 401
        await hass.config_entries.async_remove(entry.entry_id)

async def test_role_mismatch_can_retry_without_claiming(hass, hass_client):
    client = await setup(hass, hass_client)
    started = await start(hass, client)
    flow = await hass.config_entries.flow.async_init('bowpane', context={'source':'user'})
    result = await hass.config_entries.flow.async_configure(flow['flow_id'],
        {'name':'Synthetic retry', 'code':started['code'], 'role':'tv_display'})
    assert result['type'] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(flow['flow_id'],
        {'name':'Synthetic retry', 'code':started['code'], 'role':'mac_agent'})
    assert result['type'] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert (await post(client, 'confirm', started['secret'])).status == 200

async def test_revoking_one_device_preserves_another(hass, hass_client):
    client = await setup(hass, hass_client)
    first = await start(hass, client)
    first_entry = await approve(hass, first)
    assert (await post(client, 'confirm', first['secret'])).status == 200
    second = await start(hass, client)
    await approve(hass, second)
    assert (await post(client, 'confirm', second['secret'])).status == 200
    await hass.config_entries.async_remove(first_entry.entry_id)
    assert (await post(client, 'v2_health', first['secret'])).status == 401
    assert (await post(client, 'v2_health', second['secret'])).status == 200
    assert (await post(client, 'configuration', second['secret'])).status == 403

async def test_tv_still_requires_camera_selection(hass, hass_client):
    client = await setup(hass, hass_client)
    started = await start(hass, client, 'tv_display')
    flow = await hass.config_entries.flow.async_init('bowpane', context={'source':'user'})
    result = await hass.config_entries.flow.async_configure(flow['flow_id'],
        {'name':'Synthetic TV', 'code':started['code'], 'role':'tv_display'})
    assert result['type'] is FlowResultType.FORM
    assert result['errors'] == {'base':'invalid_pairing'}
    assert (await post(client, 'confirm', started['secret'])).status == 410
