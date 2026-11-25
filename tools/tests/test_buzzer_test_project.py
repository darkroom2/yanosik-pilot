from pathlib import Path
import unittest


class BuzzerTestProject(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[2]
        self.project = self.root / "firmware" / "buzzer-test"

    def test_pwm_overlay_maps_physical_pins_to_p0_05_and_p0_06(self):
        overlay = (self.project / "zephyr" / "nrf52dk_nrf52832.overlay").read_text()

        self.assertIn("NRF_PSEL(PWM_OUT0, 0, 5)", overlay)
        self.assertIn("NRF_PSEL(PWM_OUT1, 0, 6)", overlay)
        self.assertIn("&uart0", overlay)
        self.assertIn('status = "disabled"', overlay)

    def test_application_uses_opposite_channels_at_2khz(self):
        main = (self.project / "src" / "main.c").read_text()

        self.assertIn("PWM_DT_SPEC_GET(DT_ALIAS(buzzer_pwm_a))", main)
        self.assertIn("PWM_DT_SPEC_GET(DT_ALIAS(buzzer_pwm_b))", main)
        self.assertIn("buzzer_tone(2000, 500)", main)
        self.assertIn("k_msleep(1000)", main)
        self.assertIn("period_ns / 2U", main)

    def test_project_generates_zephyr_bin_like_ble_zephyr(self):
        platformio = (self.project / "platformio.ini").read_text()
        post_build = self.project / "post_build_bin.py"

        self.assertIn("post:post_build_bin.py", platformio)
        self.assertTrue(post_build.is_file())
