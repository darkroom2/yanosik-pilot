import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import read_rtt_logs


class ReadRttLogsHelpers(unittest.TestCase):
    def test_extracts_wrapped_ring_buffer(self):
        ram = bytearray(512)
        base = 0x40
        ram[base:base + 4] = b"SEGGER RTT\0"
        buffer_address = 0x20000000
        buffer_size = 8
        buffer_offset = 0x100
        ram[buffer_offset:buffer_offset + 8] = b"3456ABCD"
        ring = read_rtt_logs.extract_ring(
            ram,
            ram_address=0x20000000,
            buffer_address=0x20000100,
            buffer_size=buffer_size,
            read_offset=6,
            write_offset=4,
        )
        self.assertEqual(ring, b"CD3456")

    def test_clean_rtt_log_removes_terminal_color_sequences(self):
        raw = b"\x1b[0m<inf> ble_zephyr: BLE advertising started.\x1b[0m\r\n"
        self.assertIn(
            "BLE advertising started",
            read_rtt_logs.clean_rtt_log(raw),
        )
