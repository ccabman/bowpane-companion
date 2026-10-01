# Beta release checklist

## Before public upload

- [x] Owner confirms public ccabman/bowpane-companion and MIT; license included.
- [ ] Review tracked files for secrets, household details, private pictures and TV app source.
- [ ] Pass companion tests and verify fresh-install instructions.

## GitHub beta

- [x] Publish only this companion directory as the repository root.
- [x] Enable issues/private vulnerability reporting; add description and topics.
- [x] Pass tests, hassfest and HACS checks. Brands validation is explicitly deferred for the custom-repository beta.
- [ ] Test HACS download/install on a disposable Home Assistant instance.
- [ ] Test pairing, changes, restart persistence, removal/disable revocation, and update from 0.1.3.
- [ ] Publish a versioned prerelease explaining how testers obtain the separate TV app.

## Default HACS listing, later

- [ ] Complete security and supported-version checks.
- [ ] Register home-assistant/brands assets under the integration domain.
- [ ] Remove temporary brands ignore and pass full validation.
- [ ] Submit to hacs/default only when requested by the owner.

Unit tests use mocks. Earlier development included physical-TV pairing and an isolated HA test, but a packaged-release install still needs verification.

First public validation: https://github.com/ccabman/bowpane-companion/actions/runs/36807818210
Hassfest passed with a configuration-schema warning; resolve before a tagged beta release. Workflow dependencies also report a Node runtime deprecation warning.
