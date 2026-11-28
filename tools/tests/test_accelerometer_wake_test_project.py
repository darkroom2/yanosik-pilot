from pathlib import Path
import unittest


class AccelerometerWakeTestProject(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[2]
        self.project = self.root / "firmware" / "accelerometer-wake-test"

    def test_project_is_template_copy_with_wake_test_configuration(self):
        for relative_path in (
            "platformio.ini",
            "post_build_bin.py",
            "zephyr/CMakeLists.txt",
            "zephyr/prj.conf",
            "zephyr/app.overlay",
            "src/main.c",
        ):
            self.assertTrue((self.project / relative_path).is_file())

        cmake = (self.project / "zephyr" / "CMakeLists.txt").read_text()
        self.assertIn("project(accelerometer_wake_test)", cmake)

    def test_main_contains_reset_fifo_sleep_to_wake_setup_and_system_off(self):
        main = (self.project / "src" / "main.c").read_text()

        self.assertIn("0x19", main)
        self.assertIn("NRF_POWER->RESETREAS", main)
        self.assertIn("NRF_POWER->RESETREAS = resetreas", main)
        self.assertIn("RESETREAS_OFF", main)

        for pin in ("P0.03", "P0.11", "P0.12", "P0.13", "P0.14",
                    "P0.17", "P0.18", "P0.19"):
            self.assertIn(pin, main)

        for register_value in (
            "0x0F", "0x33", "0x20", "0x57", "0x21", "0x09",
            "0x22", "0x40", "0x23", "0x80", "0x24", "0x40",
            "0x2E", "0xC0", "0x3E", "0x08", "0x3F", "0x26",
            "0x32", "0x33", "0x02", "0x30", "0x2A", "0x31", "0x26",
            "0x2F", "0x28", "0x80", "0x1F", "0x00", ">> 6",
        ):
            self.assertIn(register_value, main)

        for low_power_operation in (
            "DCDCEN",
            "SYSTEMOFF",
            "TASKS_STOP",
            "SENSE_HIGH",
            "INPUT_DISCONNECT",
            "NRF_GPIO_PIN_PULLUP",
            "k_msleep(50)",
        ):
            self.assertIn(low_power_operation, main)

        self.assertIn("lis2dh_read_fifo(i2c,", main)
        self.assertIn("lis2dh_rearm_fifo(i2c,", main)
        self.assertIn("wait_for_int1_low()", main)

    def test_configuration_is_rtt_only_and_thinned(self):
        prj = (self.project / "zephyr" / "prj.conf").read_text()
        for setting in (
            "CONFIG_CONSOLE=y",
            "CONFIG_USE_SEGGER_RTT=y",
            "CONFIG_RTT_CONSOLE=y",
            "CONFIG_LOG=y",
            "CONFIG_LOG_BACKEND_RTT=y",
            "CONFIG_GPIO=y",
            "CONFIG_I2C=y",
        ):
            self.assertIn(setting, prj)

        overlay = (self.project / "zephyr" / "app.overlay").read_text()
        self.assertIn("NRF_PSEL(TWIM_SCL, 0, 12)", overlay)
        self.assertIn("NRF_PSEL(TWIM_SDA, 0, 11)", overlay)
        self.assertNotIn("P0.14", overlay)
