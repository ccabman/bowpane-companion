# Protocol v2 and read-only health prototype

Development branch `dev/protocol-v2-health`, based on companion commit
`09d07d6c543ccaddd379fb87d8f6a6e7a57c973d`. No version bump, release, or deployment.

## Contract

Native routes remain POST `/api/bowpane/{action}`, using trusted HTTPS and
`X-BowPane-Key`. Any Origin header (including empty) is rejected. Responses use
Cache-Control: no-store. Browser cards must use HA's own authenticated context.

`v2_start` accepts exactly `{"versions":[2],"role":"mac_agent"}` or the
`tv_display` role. It selects protocol 2 and returns protocolVersion, role,
capabilities, secret, code and expiresIn. Unsupported versions/roles and
client-supplied capabilities fail closed. Five-minute claims, five-attempt
lockout, start throttling and single use are shared with v1.

The HA administrator enters the code and explicitly selects the matching role.
Wrong code/role errors can be corrected in the same form. A TV still requires
one to four cameras. A Mac needs no cameras; TV selections are ignored for it.
The client must then confirm. V2 status/confirmation responses wrap the approved
protocolVersion, role, capabilities and configuration (null for Mac). V1 wire
shapes and stored entries are unchanged; no migration adds privileges.

| Role | Granted capabilities |
| --- | --- |
| Existing v1 TV | configuration.read, camera.stream |
| v2 tv_display | configuration.read, camera.stream |
| v2 mac_agent | health.read |

Permissions are server-defined and persisted per entry. Entitlement reports are
UI hints only. Mac options cannot turn it into a TV; re-pair to change its role.
Remove its HA entry to revoke new API access. Existing HA-issued HLS links may
remain usable until HA expires them, just as before.

`v2_health` requires a confirmed Mac credential. It returns protocolVersion=2
and independent photos/calendars/music records. Production collectors are not
connected: each currently reports state=unsupported, reason=adapter_not_connected,
lastAttempt=null and lastSuccess=null. Reachability is not sync success.

The internal health collector scaffold runs asynchronous adapters independently,
limits each to one second and emits only allowlisted state/reason fields.
Exceptions, arbitrary strings and extra fields are discarded. No collector
registration or health-report ingestion API exists. Timestamps and sync metadata
remain null until their validation and actual collectors are implemented.

JSON input operations require Content-Length, enforce actual byte bounds and a
five-second read deadline, and reject Content-Encoding other than identity.
Limits: negotiation and entitlement report 512 bytes; stream request 1024 bytes.
Existing native clients send ordinary uncompressed JSON.

No publishing, uploads, photo/Favorite writes, calendar mutation, playback
controls or arbitrary HA service endpoint is implemented.

## Tests and acceptance

See SECURITY_REVIEW.txt for findings and VALIDATION.txt for concrete evidence.
The runtime suites pass on HA 2026.9.0 and 2026.10.2.
The default runtime suite uses real HA with synthetic entries and loopback HTTP;
HA's trusted-proxy middleware supplies HTTPS for those route tests. A separate
two-process test uses real TLS and HA's configuration storage. The opt-in native
lab uses TLS, a fresh TV simulator and generated video.

Run unit tests separately from runtime tests: the original unittest adapter
suite installs minimal HA/aiohttp module doubles and must not share a process
with pytest's actual HA imports.

```
python -m unittest discover -s tests -v
python -m pip install -r requirements-runtime-test.txt
python -m pytest -q runtime_tests
```

The native lab is opt-in, requires Xcode and an isolated copy of the existing
TV project, a temporary localhost certificate trusted only by a fresh simulator,
and a generated test-pattern video. It runs only CompanionTests and
CompanionLabTests; it never runs the household-oriented LivePlaybackTests.
The TV source/tests are unchanged, and no app credential is saved to Keychain.

## Remaining deployment gates

- Run Linux GitHub CI, including the full HACS action, against the reviewed ref.
- Confirm the native release repository/build identity; simulator source parity
  does not identify the exact binary installed on the household TV.
- Review the actual HA frontend visually on a supported deployment platform.
  The real serialized flow schemas/selectors and translations are validated;
  a browser screenshot review has not been performed.
- Review and approve a targeted companion backup, install and rollback procedure
  before household deployment. Do not restore whole-house YAML as a rollback.
- Keep live health collectors, Mac packaging and photo transport migration as
  separate implementation work; do not describe placeholder health as live sync.

Calendar/MA credentials and the Apple Music developer-key workaround remain
untouched. Developer signing credentials and subscriber authorization are still
separate, and their lifecycle inspection remains later work. Existing Photos,
frame transport and frame maintenance remain authoritative.
