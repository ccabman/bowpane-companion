# BowPane Companion

Local Home Assistant pairing and configuration for the BowPane Apple TV app.

**Development beta.** The compatible Apple TV app is distributed separately and its source is not included. This is not yet a default HACS listing or a claim of App Store availability.

## Requirements

- Home Assistant 2026.9.0 or later. Development testing covered the 2026.9 series, not all future releases.
- Administrator access and a trusted HTTPS Home Assistant address reachable from the TV.
- One to four camera entities capable of HLS streaming; sensors are optional.
- A compatible BowPane TV build. Raw RTSP and WebRTC URLs are not supported by this companion/app path.

Do not expose Home Assistant publicly solely for this integration. Self-signed certificates are not bypassed; configure trusted proxies correctly if HTTPS terminates upstream.

## Install

Back up Home Assistant first. Add https://github.com/ccabman/bowpane-companion in HACS → Custom repositories, type Integration. Download BowPane Companion and restart Home Assistant when convenient. Fresh packaged installation testing remains a beta release gate; see the checklist below.

Alternatively, copy `custom_components/bowpane` into your Home Assistant configuration's `custom_components` directory and restart.

### Upgrading the early HomeGlance prototype

Version 0.2.0 changes the integration domain and folder from `homeglance` to `bowpane`. This requires fresh pairing; old entries do not migrate automatically. Back up first and record your selected cameras, sensors, and display settings. Install BowPane through HACS, restart, and install a TV build supporting the new domain. Start pairing from the TV, add the new BowPane integration in Home Assistant, and approve on the TV. Reapply display settings and confirm playback before removing the old integration entries and old folder. Do not merely rename an installed folder. Updated TV builds keep existing saved legacy connections working until you replace them through pairing.

## Pair

1. In Home Assistant, open Settings → Devices & services → Add integration → BowPane. Enable the local pairing service if prompted.
2. On the TV, open Settings → Pair with Home Assistant, enter your HTTPS address, and start pairing.
3. Follow the TV's QR link or add another BowPane entry in Home Assistant.
4. Enter the **four-digit** code, name the TV, and select one to four cameras and up to four Glance sensors. Optional full-screen camera entities should show higher-quality feeds of the same cameras.
5. Review and approve on the TV within five minutes.

No cloud BowPane account or general Home Assistant access token is needed. The code is a session locator, not an access credential.

## Configure later

Open Settings → Devices & services → BowPane → your TV → Configure. Select the TV entry, not the pairing service. Changes normally reach the active TV within about 30 seconds without pairing again.

- Cameras: up to four grid feeds, with optional higher-quality full-screen feeds where the TV tier supports them.
- Glance: up to four sensor or binary-sensor entities.
- Screen margins: expanded view reduces the border; disable it if edges are clipped.
- Camera images: crop to fill (requires the updated TV build). Off preserves the whole image with borders where necessary; on trims the edges to fill each tile without stretching. Applies to Glance, Camera Grid, and full-screen cameras, in Free and Pro.
- Camera Grid clock: on/off, seven positions, and optional black backing, available in Free and Pro.
- Home Panel preview: title, two or three columns, clock visibility, and up to six distinct read-only sensor tiles. Not an embedded dashboard or unlimited layout editor.

The companion uses short-lived TV-reported tier hints to tailor settings. These are **not verified purchases** or a server-side paywall. Hidden Pro settings are retained when the TV is offline or reports Free. Keep the TV app open and reopen Configure to refresh the form. Production purchases/restoration are not implemented here.

In compatible TV builds, swipe deliberately left/right to move between Glance, Camera Grid, and Home Panel (Pro). Directional clicks still move camera focus in Glance. Press Back/Menu for Settings or direct view selection. Camera Grid is view-only; use Glance to expand a camera. In full screen, left/right cycles cameras and Back returns.

Companion 0.2.1 adds **Opening screen** under the TV entry's Configure form. The choice applies on the next app launch, not immediately while watching. Home Panel requires Pro; the TV falls back to Glance when unavailable. The camera clock settings now control both Camera Grid and full-screen cameras. These features require the updated TV build.

## Troubleshooting

- No code/access refused: check installation, restart, HTTPS address and proxy settings. Start a fresh session if expired.
- Code rejected: codes expire after five minutes and are single-use. Five incorrect claims trigger a five-minute lockout.
- Cannot edit: Configure the TV entry, not the pairing service.
- Pro fields missing: open the TV app and reopen Configure. Reports expire after two minutes and on restart.
- Camera unavailable: verify that entity streams in Home Assistant. Entity selection alone does not guarantee codec/network compatibility.
- Old branding: refresh the frontend. A `homeglance` folder or old entry belongs to the pre-0.2.0 prototype; follow the upgrade steps above.

## Privacy and security

Access is limited to each TV's selected entities. There are no service-call endpoints or uploads to a BowPane server. HTTPS and a separate random 256-bit credential protect requests. Home Assistant stores its hash; the TV stores the credential in Keychain.

Removing or disabling a TV entry revokes new requests. Already-issued HLS links may remain usable until Home Assistant expires them. The optional QR redirect visits My Home Assistant but carries no household address or TV credential; manual pairing avoids that external redirect.

See [SECURITY.md](SECURITY.md). This beta has not had an independent security audit.

## Development and release status

Run `python3 -m unittest discover -s tests -v`. Tests use policy tests and lightweight Home Assistant adapters, not a full runtime certification. GitHub workflows additionally run hassfest and HACS checks.

See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) and [CHANGELOG.md](CHANGELOG.md). This companion is licensed under [MIT](LICENSE); the separate private Apple TV app is excluded.
