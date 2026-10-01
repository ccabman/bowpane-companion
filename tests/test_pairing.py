import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("pairing", Path(__file__).parents[1] / "custom_components/bowpane/pairing.py")
pairing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pairing)


class PairingTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000
        self.broker = pairing.Pairings(lambda: self.now)

    def test_secret_is_hashed_and_not_the_code(self):
        row = self.broker.start()
        self.assertEqual(len(row["code"]), 4)
        self.assertGreaterEqual(len(row["secret"]), 40)
        self.assertNotIn(row["secret"], repr(self.broker.pending))
        self.assertIsNone(self.broker.get(row["code"]))

    def test_expiration(self):
        row = self.broker.start()
        self.now += 300
        self.assertIsNone(self.broker.get(row["secret"]))
        with self.assertRaises(ValueError): self.broker.claim(row["code"], "entry")

    def test_one_time_claim(self):
        row = self.broker.start()
        self.broker.claim(row["code"], "entry")
        with self.assertRaises(ValueError): self.broker.claim(row["code"], "other")

    def test_cancel(self):
        row = self.broker.start()
        self.broker.cancel(row["secret"])
        self.assertIsNone(self.broker.get(row["secret"]))

    def test_throttle_and_capacity(self):
        self.broker.start()
        with self.assertRaises(ValueError): self.broker.start()
        for _ in range(7):
            self.now += 5
            self.broker.start()
        self.now += 5
        with self.assertRaises(ValueError): self.broker.start()

    def test_scope_validation(self):
        pairing.validate_selection([{"entity":"camera.door","main":"camera.high"}], ["sensor.temp"])
        for cameras, sensors in [([], []), ([{"entity":"switch.lock"}], []), ([{"entity":"camera.door"}], ["lock.front"]), ([{"entity":"camera.door"}] * 5, [])]:
            with self.assertRaises(ValueError): pairing.validate_selection(cameras, sensors)

    def test_incorrect_claims_are_limited(self):
        row = self.broker.start()
        for _ in range(5):
            with self.assertRaises(ValueError): self.broker.claim("invalid", "entry")
        with self.assertRaises(ValueError): self.broker.claim(row["code"], "entry")
        self.now += 301
        fresh = self.broker.start()
        self.assertEqual(self.broker.claim(fresh["code"], "entry"), pairing.digest(fresh["secret"]))

    def test_panel_scope_and_layout(self):
        valid = {"title": "My home", "columns": 3, "show_clock": True, "entities": ["sensor.temp", "binary_sensor.door"]}
        pairing.validate_panel(valid)
        pairing.validate_panel({**valid, "entities": []})
        for change in [{"entities": ["light.room"]}, {"entities": ["sensor.temp"] * 2},
                       {"entities": [f"sensor.t{i}" for i in range(7)]}, {"columns": 4},
                       {"show_clock": "true"}, {"title": " "}]:
            with self.assertRaises(ValueError): pairing.validate_panel({**valid, **change})

if __name__ == "__main__": unittest.main()
