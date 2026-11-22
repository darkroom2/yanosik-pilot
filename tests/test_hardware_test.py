import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, "tools")

import hardware_test


class HardwareTestHelpers(unittest.TestCase):
    def test_led_masks_are_active_low(self):
        self.assertEqual(hardware_test.led_on_mask(17), 1 << 17)
        self.assertEqual(hardware_test.led_off_mask(17), 1 << 17)

    def test_button_state_extracts_independent_bits(self):
        self.assertEqual(hardware_test.input_bit(0x00006000, 13), 1)
        self.assertEqual(hardware_test.input_bit(0x00004000, 14), 1)
        self.assertEqual(hardware_test.input_bit(0x00002000, 14), 0)

    def test_destructive_commands_are_excluded(self):
        destructive = {"erase_all", "page_erase", "flash_file", "restore"}
        self.assertTrue(destructive.isdisjoint(hardware_test.ALLOWED_COMMANDS))

    def test_buzzer_pin_parser_rejects_invalid_pins(self):
        with self.assertRaises(ValueError):
            hardware_test.parse_buzzer_pins("15,bad")
        with self.assertRaises(ValueError):
            hardware_test.parse_buzzer_pins("32")

    @patch("hardware_test.wait_for_user", return_value="yes")
    @patch("hardware_test.swd_write")
    def test_led_sequence_checks_each_color_separately(
        self, swd_write_mock, wait_mock
    ):
        hardware_test.test_leds("http://swd.local", 0.01)

        writes = [
            call.args[1:] for call in swd_write_mock.call_args_list
        ]
        self.assertIn((0x5000050C, 1 << 18), writes)
        self.assertIn((0x5000050C, 1 << 19), writes)

    @patch("hardware_test.urlopen")
    def test_init_posts_init_command(self, urlopen_mock):
        urlopen_mock.return_value.__enter__.return_value.read.return_value = b"Ok"

        self.assertTrue(hardware_test.swd_init("http://swd.local"))

        request = urlopen_mock.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertIn("/set_swd?cmd=init", request.full_url)


if __name__ == "__main__":
    unittest.main()
