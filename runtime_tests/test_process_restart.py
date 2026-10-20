"""A full two-process HA boot/restart with synthetic persisted pairings."""
import asyncio
import ipaddress
import shutil
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


@pytest.mark.asyncio
async def test_confirmed_and_unconfirmed_pairings_across_process_restart(tmp_path):
    source = Path(__file__).parents[1] / 'custom_components' / 'bowpane'
    shutil.copytree(source, tmp_path/'custom_components'/'bowpane', dirs_exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'BowPane synthetic restart lab')])
    now = datetime.now(UTC)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=1))
        .not_valid_after(now+timedelta(days=1)).add_extension(x509.SubjectAlternativeName([
            x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]), critical=False)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None),critical=True).sign(key,hashes.SHA256()))
    (tmp_path/'localhost.pem').write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    private = tmp_path/'localhost.key'
    private.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    private.chmod(0o600)
    for mode in ['seed', 'verify']:
        process = await asyncio.create_subprocess_exec(sys.executable,
            str(Path(__file__).with_name('restart_worker.py')), mode, str(tmp_path),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            async with asyncio.timeout(90):
                stdout, stderr = await process.communicate()
        except TimeoutError:
            process.kill()
            await process.wait()
            pytest.fail('Isolated restart process timed out')
        # Do not echo child output on failure: it might contain credentials.
        error_log = tmp_path / (mode+'-private-error.log')
        error_log.write_bytes(stderr)
        error_log.chmod(0o600)
        assert process.returncode == 0, 'Isolated '+mode+' process failed'
        assert (mode+' process passed').encode() in stdout
