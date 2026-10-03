# BowPane Companion

Local Home Assistant pairing and configuration for the BowPane Apple TV app.

**Development beta.** The compatible Apple TV app is distributed separately and its source is not included. This is not yet a default HACS listing or a claim of App Store availability.

## Requirements

- Home Assistant 2026.9.0 or later. Development testing covered the 2026.9 series, not all future releases.
- Administrator access and a trusted HTTPS Home Assistant address reachable from the TV.
- One to four camera entities capable of HLS streaming; sensors are optional.
- A compatible BowPane TV build. Raw RTSP and WebRTC URLs are not supported by this companion/app path.

You will use three separate pieces:

- **BowPane on Apple TV** displays your cameras and sensors. During this beta, install the TV app through TestFlight using the invitation provided to you; installing this repository does not install the TV app.
- **HACS** downloads and updates the companion files in Home Assistant.
- **The BowPane integration** enables pairing and lets you configure each TV in Home Assistant.

For camera crop-to-fill, use companion **0.2.2 or later** and TV build **1.0 (5) or later**. Check the installed TV build in TestFlight. The companion and TV app have separate version numbers and update independently.

Do not expose Home Assistant publicly solely for this integration. Self-signed certificates are not bypassed; configure trusted proxies correctly if HTTPS terminates upstream.

## Install

### 1. Prepare Home Assistant and your cameras

1. Make a Home Assistant backup before installing or updating custom integrations.
2. Confirm HACS is installed. If it is not, follow the [official HACS setup instructions](https://www.hacs.dev/docs/use/).
3. Sign in to Home Assistant as an administrator on your phone or computer.
4. Confirm each camera you want to display already works in Home Assistant. BowPane does not install camera integrations or discover cameras directly.
5. Have your trusted **HTTPS Home Assistant address** ready. It must be reachable from the Apple TV, not just from your phone. Enter the server address, such as `https://ha.example.com`, not a dashboard URL, camera URL, or SSH address. Include an HTTPS port only if your server actually uses that port.

Working video in Home Assistant is a useful first check, but does not guarantee HLS/codec compatibility with Apple TV. Do not open new internet-facing ports solely for BowPane.

### 2. Download the companion through HACS

BowPane is currently a **custom repository**, not a default HACS listing. A search for BowPane will not find it until you add the repository.

1. Open **HACS** in Home Assistant.
2. Open the **⋮** menu and select **Custom repositories**.
3. Paste `https://github.com/ccabman/bowpane-companion` into the repository field.
4. Choose **Integration** as the type/category, then select **Add**.
5. Close the custom-repository dialog and search HACS for **BowPane**. Clear filters if it does not appear.
6. Open **BowPane Companion**, select **Download**, and install the latest release. Menu wording can vary with your HACS version.
7. **Restart Home Assistant**, not just the browser or phone app. Wait until Home Assistant is fully available again. Downloading files alone does not load the integration.

### 3. Enable the pairing service

1. Open **Settings → Devices & services** in Home Assistant.
2. Select **Add integration**, search for **BowPane**, and select it.
3. If prompted to enable the local pairing service, submit that form. You should now have a **BowPane pairing service** entry.
4. Leave that service installed. It is separate from your individual TV entry and is needed for new pairing sessions.

If BowPane is not listed under Add integration, verify the HACS download completed and Home Assistant was restarted. A missing HACS icon does not by itself mean installation failed.

### Manual installation (alternative to HACS)

Copy this repository's `custom_components/bowpane` directory into your Home Assistant configuration directory so the manifest is at `custom_components/bowpane/manifest.json`. Do not nest the entire repository inside that directory. Restart Home Assistant, then enable the pairing service as above. Manual installation does not register the repository with HACS for update tracking.

### Upgrading the early HomeGlance prototype

Version 0.2.0 changes the integration domain and folder from `homeglance` to `bowpane`. This requires fresh pairing; old entries do not migrate automatically. Back up first and record your selected cameras, sensors, and display settings. Install BowPane through HACS, restart, and install a TV build supporting the new domain. Start pairing from the TV, add the new BowPane integration in Home Assistant, and approve on the TV. Reapply display settings and confirm playback before removing the old integration entries and old folder. Do not merely rename an installed folder. Updated TV builds keep existing saved legacy connections working until you replace them through pairing.

## Pair

### 4. Start pairing on Apple TV

1. Install/open the compatible BowPane TV app.
2. Open the TV app's **Settings → Pair with Home Assistant**. From a viewing screen, press Back/Menu to open the navigation menu, then choose Settings.
3. The initial installation QR links to this README. It is **not** the pairing code.
4. Enter your HTTPS Home Assistant server address and choose **Start pairing**.
5. Keep the TV app open. A **four-digit code**, expiry countdown, and setup QR should appear. If you see an error instead, use Troubleshooting below; no pairing session has successfully started yet.

### 5. Approve the TV in Home Assistant

1. Scan the setup QR on your phone. It opens the Home Assistant integration setup through My Home Assistant; check that it opens the correct Home Assistant instance.
2. Alternatively, open **Settings → Devices & services → Add integration → BowPane** manually. With the pairing service already enabled, this opens the TV pairing form.
3. Give the TV a recognizable name, such as **Living room TV**.
4. Enter the four-digit code currently shown on the TV, including any leading zero.
5. Select **Grid camera 1**. You must choose at least one camera; cameras 2–4 are optional. The numbered selections define the display order: top left, top right, bottom left, bottom right.
6. Optional **Full-screen camera** selections should be higher-quality entities for the corresponding grid camera, not unrelated cameras. You can leave them empty initially. Availability depends on the TV's tier.
7. Optionally select up to four Glance sensor or binary-sensor entities. Starting with one camera and no sensors is fine; you can add more later without re-pairing.
8. Submit the form before the code expires. Codes are single-use and expire after five minutes; use the TV's countdown as your guide. If it expires, start a fresh pairing session and use its new code.

### 6. Confirm on the TV

1. Return to the TV and review the proposed TV name, cameras, and sensors.
2. Choose the TV's approval action. **Approval in Home Assistant alone does not finish pairing.**
3. Wait for playback and sensor readings. Allow about 30 seconds for configuration updates while the app is active; camera startup may take additional time.
4. Test a camera in Glance, open it full screen, and return. Confirm the selected sensors show sensible readings.
5. Open the paired TV's Configure form to set your preferred display options below.

Avoid repeatedly submitting the same expired code. If pairing fails, keep the error message and check the troubleshooting steps rather than deleting all your camera integrations.

No cloud BowPane account or general Home Assistant access token is needed. The code is a session locator, not an access credential.

## Configure later

Open Settings → Devices & services → BowPane → your TV → Configure. Select the TV entry, not the pairing service. Changes normally reach the active TV within about 30 seconds without pairing again.

Save/submit the form after editing. Keep BowPane open on the TV while waiting for changes. Reopen Configure if you need to verify saved selections. Adding a second TV uses a new pairing session and its own configuration.

- Cameras: up to four grid feeds, with optional higher-quality full-screen feeds where the TV tier supports them.
- Glance: up to four sensor or binary-sensor entities.
- Weather widget (companion **0.2.3+** and TV build **1.0 (6)+**): toggle **Show weather beneath the Glance clock**, select a **Primary weather entity** (`weather.*`), and optionally select an **Indoor house temperature sensor** with device class `temperature`. Current conditions, outside temperature, and optional indoor temperature appear beneath the clock; all four custom sensor slots remain available below. Available in Free and Pro. Uses your existing Home Assistant weather provider, not a new BowPane weather account. Disabled by default; no re-pairing is needed when configuring it later. Missing readings display as unavailable, not as zero. Units are preserved independently from each selected entity.
- Screen margins: expanded view reduces the border; disable it if edges are clipped.
- Camera images: crop to fill (requires the updated TV build). Off preserves the whole image with borders where necessary; on trims the edges to fill each tile without stretching. Applies to Glance, Camera Grid, and full-screen cameras, in Free and Pro.
- Camera Grid clock: on/off, seven positions, and optional black backing, available in Free and Pro.
- Home Panel preview: title, two or three columns, clock visibility, and up to six distinct read-only sensor tiles. Not an embedded dashboard or unlimited layout editor.

The companion uses short-lived TV-reported tier hints to tailor settings. These are **not verified purchases** or a server-side paywall. Hidden Pro settings are retained when the TV is offline or reports Free. Keep the TV app open and reopen Configure to refresh the form. Production purchases/restoration are not implemented here.

In compatible TV builds, swipe deliberately left/right to move between Glance, Camera Grid, and Home Panel (Pro). Directional clicks still move camera focus in Glance. Press Back/Menu for Settings or direct view selection. Camera Grid is view-only; use Glance to expand a camera. In full screen, left/right cycles cameras and Back returns.

Companion 0.2.1 adds **Opening screen** under the TV entry's Configure form. The choice applies on the next app launch, not immediately while watching. Home Panel requires Pro; the TV falls back to Glance when unavailable. The camera clock settings now control both Camera Grid and full-screen cameras. These features require the updated TV build.

### Display choices explained

- **Fit (Crop to fill off):** preserves the entire camera image without stretching. Square doorbell feeds may have side bands in a rectangular tile; wide feeds may have top/bottom bands.
- **Crop to fill on:** fills each tile without stretching by trimming image edges. For a square doorbell in a wide tile, some top/bottom content is lost. This applies to all camera views; it is a per-TV setting, not a separate setting for each camera.
- **Expanded screen margins:** uses more of the display. Disable it if your television clips the edges. This is separate from camera image cropping.
- **Camera clock:** controls visibility, location, and optional black backing in Camera Grid and single-camera view. The Glance sidebar has its own clock.
- **Opening screen:** choose Glance, Camera Grid, or the available Home Panel option. It applies the next time the app opens, not as an immediate view change.

### Remote navigation (TV build 5)

- Swipe deliberately left/right to change dashboard views. Supported input includes the physical Siri Remote and the phone's Apple TV Remote.
- In Glance, directional clicks move camera focus; Select opens a configured camera full screen.
- Camera Grid is a view-only full-screen grid. Use Glance when you want to select a single camera.
- In single-camera view, Left/Right cycles configured cameras; Back returns to the dashboard.
- Camera labels and hints fade after inactivity. Remote input brings them back; the enabled camera clock stays visible.
- From a dashboard, Back opens the navigation menu. **Back again from that menu returns to Apple TV Home.** Choose Return to cameras to dismiss the menu without leaving BowPane.

## Updates and reinstalling

### Companion updates

1. Open BowPane Companion in HACS and review the release notes.
2. Install the new release when available.
3. Restart Home Assistant to load the updated Python integration.
4. Reopen BowPane on the TV and allow configuration to refresh.

Normal companion updates within the `bowpane` domain do **not** require re-pairing. A domain migration or removal of the paired TV entry is different; see the prototype upgrade instructions above.

HACS supplies an update entity for downloaded repositories, typically `update.bowpane_companion_update` (the name can vary). Make sure it is enabled if updates do not appear. BowPane is a custom repository, whose automatic refresh can take up to 48 hours. Open its HACS repository page or use **⋮ → Update information** to check sooner. An installed version matching the latest release will not show an available update. See [HACS update entities](https://www.hacs.dev/docs/use/entities/update/) and [refresh timing](https://www.hacs.dev/docs/faq/data_sources/).

### TV app updates and reinstallation

Update the TV app separately through TestFlight during the beta. A HACS update does not update the Apple TV app, and a TV-only fix may have no accompanying companion release.

Deleting and reinstalling the TV app may leave its secure Keychain connection intact. Do not assume reinstalling alone is a completely fresh setup. Removing the paired TV entry in Home Assistant revokes its access; start a new pairing session in the TV app to replace the saved connection. Removing only the pairing service is not a substitute for revoking the individual TV entry. Record your camera/display selections before deliberately removing an entry.

## Troubleshooting

- No code/access refused: check installation, restart, HTTPS address and proxy settings. Start a fresh session if expired.
- Code rejected: codes expire after five minutes and are single-use. Five incorrect claims trigger a five-minute lockout.
- Cannot edit: Configure the TV entry, not the pairing service.
- Pro fields missing: open the TV app and reopen Configure. Reports expire after two minutes and on restart.
- Camera unavailable: verify that entity streams in Home Assistant. Entity selection alone does not guarantee codec/network compatibility.
- Old branding: refresh the frontend. A `homeglance` folder or old entry belongs to the pre-0.2.0 prototype; follow the upgrade steps above.

### HACS search shows no BowPane results

Add this repository as a custom repository of type Integration first, then clear HACS search filters and search again. Being public on GitHub does not automatically put it in the default HACS catalog.

### Companion unavailable, access refused, or no pairing code

Check the server address, trusted HTTPS certificate, companion installation, Home Assistant restart, and enabled pairing service. SSH ports are not Home Assistant HTTPS ports. If you removed the old TV entry, its stored credential is no longer valid: start a fresh pairing session. For a TLS proxy, verify Home Assistant's trusted-proxy configuration and that the TV can reach the external address. Do not disable certificate verification as a workaround.

### Camera works in Home Assistant but not on TV

Confirm you selected the correct `camera.*` entity, and try just one camera first. Home Assistant can display camera formats that this TV playback path cannot use: BowPane requires compatible HLS video. Check camera integration streaming support, codec compatibility, and whether Home Assistant's generated stream address is reachable from the TV. A functioning pairing or sensor reading does not prove the separate video URL is reachable. Do not publish stream URLs or access tokens in an issue.

### Display option does not change the picture

Verify both companion and TV versions support the option, save the form on the correct TV entry, and wait about 30 seconds with the app open. Restart Home Assistant after companion updates, and fully close/reopen the TV app if needed. Re-pairing creates a new TV entry and may reset display options, so check Configure again afterward. Crop-to-fill and screen margins are separate controls. Opening screen only changes on the next app launch.

### Getting help

Open a [GitHub issue](https://github.com/ccabman/bowpane-companion/issues) with your Home Assistant, companion, and TV build versions; the view involved; the exact error text; and steps to reproduce. Include the camera integration/model if relevant. Redact household addresses, credentials, pairing codes, and private camera images. The companion has no general-access-token requirement; never send us a Home Assistant token.

## Privacy and security

Access is limited to each TV's selected entities. There are no service-call endpoints or uploads to a BowPane server. HTTPS and a separate random 256-bit credential protect requests. Home Assistant stores its hash; the TV stores the credential in Keychain.

Removing or disabling a TV entry revokes new requests. Already-issued HLS links may remain usable until Home Assistant expires them. The optional QR redirect visits My Home Assistant but carries no household address or TV credential; manual pairing avoids that external redirect.

See [SECURITY.md](SECURITY.md). This beta has not had an independent security audit.

## Development and release status

Run `python3 -m unittest discover -s tests -v`. Tests use policy tests and lightweight Home Assistant adapters, not a full runtime certification. GitHub workflows additionally run hassfest and HACS checks.

A user-run installation/pairing walkthrough and physical Apple TV viewing checks were reported successful on October 3, 2026 with TV build 5 and companion 0.2.2. This is beta testing evidence, not a guarantee across all camera models, networks, or Home Assistant versions.

See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) and [CHANGELOG.md](CHANGELOG.md). This companion is licensed under [MIT](LICENSE); the separate private Apple TV app is excluded.
