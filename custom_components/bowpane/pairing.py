"""Small, independently testable pairing policy. No Home Assistant dependencies."""
import hashlib
import secrets
import time


def digest(secret):
    return hashlib.sha256(secret.encode()).hexdigest()


def validate_selection(cameras, sensors):
    if not isinstance(cameras, list) or not 1 <= len(cameras) <= 4:
        raise ValueError("Select one to four cameras")
    if not isinstance(sensors, list) or len(sensors) > 4:
        raise ValueError("Select at most four sensors")
    for camera in cameras:
        if not isinstance(camera, dict) or not isinstance(camera.get("entity"), str) or not camera["entity"].startswith("camera."):
            raise ValueError("Invalid camera")
        main = camera.get("main", "")
        if main and (not isinstance(main, str) or not main.startswith("camera.")):
            raise ValueError("Invalid main camera")
    if any(not isinstance(s, str) or not s.startswith(("sensor.", "binary_sensor.")) for s in sensors):
        raise ValueError("Invalid sensor")


def validate_panel(panel):
    if not isinstance(panel, dict) or panel.get("columns") not in (2, 3) or type(panel.get("show_clock")) is not bool:
        raise ValueError("Invalid panel layout")
    if not isinstance(panel.get("title"), str) or not 1 <= len(panel["title"].strip()) <= 60:
        raise ValueError("Invalid panel title")
    tiles = panel.get("entities")
    if not isinstance(tiles, list) or len(tiles) > 6 or len(set(tiles)) != len(tiles):
        raise ValueError("Select up to six different panel sensors")
    if any(not isinstance(e, str) or not e.startswith(("sensor.", "binary_sensor.")) for e in tiles):
        raise ValueError("Panel is read-only sensor data")


class Pairings:
    """Five-minute, single-use claims. Secrets are never stored, only hashes."""
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.pending = {}
        self.last_start = -float("inf")
        self.failed_claims = []

    def prune(self):
        self.pending = {k: v for k, v in self.pending.items() if v["expires"] > self.clock()}

    def start(self):
        self.prune()
        if len(self.pending) >= 8 or self.clock() - self.last_start < 5:
            raise ValueError("Try again shortly")
        self.last_start = self.clock()
        secret = secrets.token_urlsafe(32)
        code = str(secrets.randbelow(10**4)).zfill(4)
        while any(v["code"] == code for v in self.pending.values()):
            code = str(secrets.randbelow(10**4)).zfill(4)
        self.pending[digest(secret)] = {"code": code, "expires": self.clock() + 300, "entry": None}
        return {"secret": secret, "code": code, "expiresIn": 300}

    def get(self, secret):
        self.prune()
        return self.pending.get(digest(secret))

    def claim(self, code, entry):
        self.prune()
        self.failed_claims = [t for t in self.failed_claims if t > self.clock() - 300]
        if len(self.failed_claims) >= 5:
            raise ValueError("Too many incorrect codes; wait five minutes")
        for key, pending in self.pending.items():
            if secrets.compare_digest(pending["code"], code) and pending["entry"] is None:
                pending["entry"] = entry
                return key
        self.failed_claims.append(self.clock())
        raise ValueError("Pairing code expired or already used")

    def cancel(self, secret):
        self.pending.pop(digest(secret), None)
