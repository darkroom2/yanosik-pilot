from pathlib import Path
import unittest


class AccelerometerTestProject(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[2]
        self.project = self.root / "firmware" / "accelerometer-test"

    def test_project_files_and_platformio_configuration(self):
        self.assertTrue((self.project / "platformio.ini").is_file())
        platformio = (self.project / "platformio.ini").read_text()
        self.assertIn("board = nrf52_dk", platformio)
        self.assertIn("framework = zephyr", platformio)
        self.assertTrue((self.project / "post_build_bin.py").is_file())

    def test_overlay_disables_hardware_accelerometer_and_keeps_led_aliases(self):
        overlay = (self.project / "zephyr" / "app.overlay").read_text()

        for pin_alias in ("led-red", "led-green", "led-blue"):
            self.assertIn(pin_alias, overlay)
        for pin in ("<&gpio0 17", "<&gpio0 18", "<&gpio0 19"):
            self.assertIn(pin, overlay)
        self.assertIn("GPIO_ACTIVE_LOW", overlay)

        self.assertIn("&spi1 {\n\tstatus = \"disabled\";", overlay)
        self.assertIn('lis2dh12: lis2dh@0 {', overlay)
        self.assertIn('status = "disabled";', overlay)
        self.assertNotIn("cs-gpios =", overlay)
        self.assertIn("accel0 = &lis2dh12", overlay)

    def test_kconfig_enables_required_drivers(self):
        prj_conf = (self.project / "zephyr" / "prj.conf").read_text()
        for setting in (
            "CONFIG_GPIO=y",
            "CONFIG_SPI=y",
            "CONFIG_SENSOR=y",
            "CONFIG_LIS2DH=y",
            "CONFIG_LIS2DH_TRIGGER_NONE=y",
            "CONFIG_LOG=y",
            "CONFIG_LOG_BACKEND_RTT=y",
        ):
            self.assertIn(setting, prj_conf)

    def test_application_scans_only_accelerometer_pins_over_spi_and_i2c(self):
        main = (self.project / "src" / "main.c").read_text()
        self.assertIn("static const uint8_t pins[] = { 3, 4, 7, 8, 12, 13 };", main)
        self.assertIn("k_busy_wait(2)", main)
        self.assertIn("0x8F", main)
        self.assertIn("0x33", main)
        self.assertIn("0x20, 0x57", main)
        self.assertIn("0xA0", main)
        self.assertIn("SPI HIT!", main)
        self.assertIn("I2C HIT!", main)
        self.assertIn("Koniec skanu. Trafienia: %d", main)
        self.assertNotIn("P0.05", main)
        self.assertNotIn("P0.06", main)
        self.assertIn("DT_ALIAS(led_red)", main)
        self.assertIn("DT_ALIAS(led_green)", main)

    def test_documentation_covers_pinout_build_flash_and_wake_future(self):
        hardware = self.project / "docs" / "hardware.md"
        readme = (self.project / "README.md").read_text()
        root_readme = (self.root / "README.md").read_text()

        self.assertTrue(hardware.is_file())
        hardware_text = hardware.read_text()
        for required in (
            "nRF52832", "QFN48", "LIS2DH12", "LGA-12",
            "P0.17", "P0.18", "P0.19", "P0.13", "P0.12",
            "P0.08", "P0.07", "P0.04", "P0.03", "P0.14", "P0.15",
            "P0.09", "P0.10", "510", "100",
        ):
            self.assertIn(required, hardware_text)

        self.assertIn("pio run", readme)
        self.assertIn("pio run -t upload", readme)
        self.assertIn("firmware/accelerometer-test", root_readme)
        self.assertIn("INT1", hardware_text)
        self.assertIn("P0.14", hardware_text)
        self.assertIn("P0.15", hardware_text)
        self.assertIn("deep sleep", hardware_text.lower())
