"""Opt-in unchanged tvOS lab test. All inputs and traffic are synthetic/loopback."""
import asyncio
import logging
import os
import ssl
from pathlib import Path
from uuid import uuid4

import pytest
from aiohttp.test_utils import TestServer
from homeassistant.auth.const import GROUP_ID_ADMIN
from homeassistant.components.camera import DATA_COMPONENT, Camera, CameraEntityFeature
from test_runtime import setup

pytestmark = [pytest.mark.asyncio, pytest.mark.skipif(
    not os.environ.get('BOWPANE_NATIVE_LAB'), reason='Opt-in local Xcode simulator lab')]

async def test_unchanged_tv_pairing_playback_and_revocation(hass, hass_client):
    private = Path(os.environ['BOWPANE_LAB_PRIVATE']).resolve()
    project = Path(os.environ['BOWPANE_LAB_TV_PROJECT']).resolve()
    device = os.environ['BOWPANE_LAB_SIMULATOR']
    # No production URLs or device identifiers are accepted by the harness.
    assert project.name == 'BowPane.xcodeproj'
    await setup(hass, hass_client)
    class SyntheticCamera(Camera):
        _attr_name = 'BowPane test pattern'
        _attr_supported_features = CameraEntityFeature.STREAM
        _attr_should_poll = False
        async def stream_source(self): return str(private / 'test-pattern.mp4')
    camera = SyntheticCamera()
    await hass.data[DATA_COMPONENT].async_add_entities([camera])
    hass.states.async_set('sensor.bowpane_lab_temperature', '21')
    assert hass.states.get('camera.bowpane_test_pattern') is not None
    admin = await hass.auth.async_create_user('Synthetic simulator admin', group_ids=[GROUP_ID_ADMIN])
    refresh = await hass.auth.async_create_refresh_token(admin, client_id='https://localhost:18123')
    token = hass.auth.async_create_access_token(refresh)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(private / 'localhost.pem', private / 'localhost.key')
    server = TestServer(hass.http.app, host='127.0.0.1', port=18123, scheme='https')
    await server.start_server(ssl=context)
    environment = os.environ.copy()
    environment['TEST_RUNNER_HOMEGLANCE_LAB_SERVER'] = 'https://localhost:18123'
    environment['TEST_RUNNER_HOMEGLANCE_LAB_ADMIN'] = token
    log = private / 'xcode-native.log'
    # Suppress HTTP debug/access logs: HLS paths contain ephemeral capabilities.
    previous_disable = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        with log.open('w') as output:
            os.chmod(log, 0o600)
            process = await asyncio.create_subprocess_exec(
                'xcodebuild', 'test', '-project', str(project), '-scheme', 'BowPane',
                '-destination', 'platform=tvOS Simulator,id='+device,
                '-derivedDataPath', str(private / 'DerivedData'),
                '-resultBundlePath', str(private / ('Native-'+uuid4().hex+'.xcresult')),
                '-only-testing:BowPaneTests/CompanionTests',
                '-only-testing:BowPaneTests/CompanionLabTests',
                'CODE_SIGNING_ALLOWED=NO',
                env=environment, stdout=output, stderr=asyncio.subprocess.STDOUT)
            try:
                async with asyncio.timeout(420):
                    code = await process.wait()
            except TimeoutError:
                process.terminate()
                await process.wait()
                pytest.fail('Xcode lab timed out; inspect the private local log')
        text = log.read_text(errors='replace')
        # The test must actually execute: a skipped native network test is no proof.
        assert code == 0, 'Native compatibility test failed; inspect private local log'
        assert "testRealPairingPlaybackAndRevocation" in text
        assert 'executed' in text.lower()
        assert "testRealPairingPlaybackAndRevocation]' passed" in text, 'Lab environment did not reach the simulator'
    finally:
        if camera.stream:
            providers = list(camera.stream.outputs().values())
            for provider in providers:
                await camera.stream.remove_provider(provider)
            await camera.stream.stop()
            await hass.async_block_till_done()
            for provider in providers:
                provider.cleanup()
        logging.disable(previous_disable)
        await server.close()
        hass.auth.async_remove_refresh_token(refresh)
