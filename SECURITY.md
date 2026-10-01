# Security

This beta has not received an independent security audit.

Do not post credentials, pairing codes, stream URLs, household pictures, or complete diagnostics in public issues. Use GitHub private vulnerability reporting if enabled. Otherwise, open a details-free issue asking for a private reporting channel.

## Boundaries

- Four-digit codes locate five-minute sessions. Home Assistant administrator approval and TV confirmation are both required.
- Device credentials contain 256 random bits; the server stores SHA-256 hashes.
- HTTPS is required; browser-Origin requests are refused.
- Only selected camera and read-only sensor entities are available. No general HA token or service-call API is exposed.
- Starts are globally limited to one per five seconds and eight pending sessions. Incorrect claims are throttled. This is not comprehensive internet-facing denial-of-service protection.
- Removal/disable stops new requests, but issued video URLs have Home Assistant-managed lifetimes.
- Tier hints are untrusted and are not purchase verification.

During beta only the latest published beta receives fixes. Back up before updating.
