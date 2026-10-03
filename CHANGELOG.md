# Changelog

## 0.2.2 — camera image fit

- Add an optional per-TV crop-to-fill setting for Glance, Camera Grid, and full-screen cameras (TV build 4 or later).
- Default to showing the complete camera image without stretching; older TV builds ignore the new setting.
- Existing pairings and camera selections remain unchanged. Fresh-install customer testing is still pending.

## 0.2.1 — opening screen

- Configure the TV's opening screen from Home Assistant without re-pairing.
- Preserve saved Pro Home Panel choices when the TV is offline or Free; the app falls back to Glance.
- Clarify that clock settings apply to Camera Grid and full-screen cameras in the updated TV app.
- Document swipe navigation and the Back/Menu shortcut. Requires TV build 2 or later.

## 0.2.0 — domain transition

- Integration folder/domain, API routes, pairing QR destination and credential header now use BowPane naming.
- Fresh pairing is required for the new integration; existing HomeGlance entries are not automatically migrated.
- Updated TV builds retain old saved connections until explicitly paired with BowPane.
- Declare UI-only configuration for Home Assistant validation.

## 0.1.4 — unreleased beta preparation

- BowPane branding and current setup documentation.
- Four-digit pairing with approval on both devices.
- Edit cameras/sensors without pairing again.
- Per-TV margins and Camera Grid clock visibility, position and backing.
- Six-tile read-only Home Panel preview and Free/Pro settings hints.
- Existing homeglance domain/API retained for compatibility.
- Test, hassfest and HACS workflow definitions.

Not a production purchase system or a default HACS listing.
