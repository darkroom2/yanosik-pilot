import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import hardware_test


class HardwareTestHelpers(unittest.TestCase):
    def test_led_masks_are_active_low(self):
        self.assertEqual(hardware_test.led_on_mask(17), 1 << 17)
        self.assertEqual(hardware_test.led_off_mask(17), 1 << 17)

    def test_button_state_extracts_independent_bits(self):
        self.assertEqual(hardware_test.input_bit(0x0000C000, 14), 1)
        self.assertEqual(hardware_test.input_bit(0x00008000, 15), 1)
        self.assertEqual(hardware_test.input_bit(0x00004000, 15), 0)

    def test_button_test_targets_confirmed_p0_14_and_p0_15(self):
        released = (1 << 14) | (1 << 15)
        with patch("hardware_test.swd_write") as write_mock, \
                patch("hardware_test.swd_read", side_effect=[released, 1 << 15, 1 << 14]) as read_mock, \
                patch("hardware_test.time.sleep"), \
                patch("builtins.input"):
            result = hardware_test.test_buttons("http://swd.local")

        self.assertEqual(
            [(call.args[1], call.args[2]) for call in write_mock.call_args_list],
            [(0x50000738, 0x0C), (0x5000073C, 0x0C)],
        )
        self.assertEqual(read_mock.call_count, 3)
        self.assertEqual(
            result,
            {
                "P0_14_released": 1,
                "P0_15_released": 1,
                "P0_14_held": 0,
                "P0_15_held": 0,
                "P0_14_bit_mask": 1 << 14,
                "P0_15_bit_mask": 1 << 15,
                "raw_released": "0x0000C000",
                "raw_button1": "0x00008000",
                "raw_button2": "0x00004000",
            },
        )

    def test_destructive_commands_are_excluded(self):
        destructive = {"erase_all", "page_erase", "flash_file", "restore"}
        self.assertTrue(destructive.isdisjoint(hardware_test.ALLOWED_COMMANDS))

    def test_buzzer_pin_parser_rejects_invalid_pins(self):
        with self.assertRaises(ValueError):
            hardware_test.parse_buzzer_pins("15,bad")
        with self.assertRaises(ValueError):
            hardware_test.parse_buzzer_pins("32")

    def test_buzzer_parser_defaults_to_confirmed_pins(self):
        args = hardware_test.build_parser().parse_args([])
        self.assertEqual(hardware_test.parse_buzzer_pins(args.buzzer_pins), [5, 6])

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
