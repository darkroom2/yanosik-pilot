from pathlib import Path
import unittest


class ZephyrTemplateProject(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[2]
        self.project = self.root / "firmware" / "zephyr-template"

    def test_cmake_has_generic_project_name_and_template_source(self):
        cmake = (self.project / "zephyr" / "CMakeLists.txt").read_text()

        self.assertIn("project(zephyr_template)", cmake)
        self.assertIn("target_sources(app PRIVATE ../src/main.c)", cmake)
        self.assertNotIn("nrf52_ble", cmake)

    def test_application_uses_led_alias_and_rtt_logging(self):
        main = (self.project / "src" / "main.c").read_text()

        self.assertIn("LOG_MODULE_REGISTER(template, LOG_LEVEL_INF)", main)
        self.assertIn("GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios)", main)
        self.assertIn("GPIO_OUTPUT_ACTIVE", main)
        self.assertIn("gpio_pin_toggle_dt", main)
        self.assertIn("k_sleep(K_SECONDS(1))", main)
        self.assertNotIn("ble_", main)

    def test_configuration_enables_rtt_and_disables_uart_console(self):
        prj_conf = (self.project / "zephyr" / "prj.conf").read_text()

        self.assertIn("CONFIG_SERIAL=n", prj_conf)
        self.assertIn("CONFIG_UART_CONSOLE=n", prj_conf)
        self.assertIn("CONFIG_USE_SEGGER_RTT=y", prj_conf)
        self.assertIn("CONFIG_RTT_CONSOLE=y", prj_conf)
        self.assertIn("CONFIG_LOG_BACKEND_RTT=y", prj_conf)
        self.assertIn("CONFIG_NRF_APPROTECT_USE_UICR=y", prj_conf)
        self.assertIn("CONFIG_NRF_APPROTECT_LOCK=n", prj_conf)

    def test_project_keeps_post_build_bin_workflow(self):
        platformio = (self.project / "platformio.ini").read_text()

        self.assertIn("framework = zephyr", platformio)
        self.assertIn("post:post_build_bin.py", platformio)
        self.assertTrue((self.project / "post_build_bin.py").is_file())

    def test_readme_documents_template_copy_and_flash_workflow(self):
        readme = (self.root / "README.md").read_text()

        self.assertIn("#### `firmware/zephyr-template`", readme)
        self.assertIn("uv run pio run --project-dir firmware\\zephyr-template -e nrf52_dk", readme)
        self.assertIn("firmware/zephyr-template/.pio/build/nrf52_dk/zephyr/zephyr.bin", readme)
