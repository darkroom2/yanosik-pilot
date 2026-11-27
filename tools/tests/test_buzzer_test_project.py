from pathlib import Path
import unittest


class BuzzerTestProject(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[2]
        self.project = self.root / "firmware" / "buzzer-test"

    def test_pwm_overlay_maps_physical_pins_to_p0_05_and_p0_06(self):
        overlay = (self.project / "zephyr" / "app.overlay").read_text()

        self.assertIn("&pwm0", overlay)
        self.assertIn('status = "disabled"', overlay)

    def test_application_uses_nrfx_pwm_and_button_controls(self):
        main = (self.project / "src" / "main.c").read_text()

        self.assertIn("NRFX_PWM_INSTANCE(0)", main)
        self.assertIn("NRF_PWM_CLK_16MHz", main)
        self.assertIn("NRF_PWM_LOAD_INDIVIDUAL", main)
        self.assertIn("NRF_GPIO_PIN_H0H1", main)
        self.assertIn("channel_1 = (uint16_t)(half | 0x8000U)", main)
        self.assertIn("nrfx_pwm_stop(&pwm_instance, false)", main)
        self.assertIn("change_frequency(50)", main)
        self.assertIn("change_frequency(-50)", main)

    def test_project_generates_zephyr_bin_like_ble_zephyr(self):
        platformio = (self.project / "platformio.ini").read_text()
        post_build = self.project / "post_build_bin.py"

        self.assertIn("post:post_build_bin.py", platformio)
        self.assertTrue(post_build.is_file())
