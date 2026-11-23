import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import extract_s132_softdevice


class ExtractS132SoftdeviceHelpers(unittest.TestCase):
    def test_extract_only_hex_from_zip_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            dumps_dir = temp / "dumps"
            dumps_dir.mkdir()

            zip_bytes = temp / "archive.zip"
            with zipfile.ZipFile(zip_bytes, "w") as archive:
                archive.writestr(
                    "s132_nrf52_2.0.1/s132_nrf52_2.0.1_softdevice.hex",
                    ":020000040001F9\n",
                )
                archive.writestr("s132_nrf52_2.0.1/readme.txt", "not extracted")

            result = extract_s132_softdevice.extract_hex(
                zip_bytes.read_bytes(), dumps_dir
            )

            self.assertEqual(result, dumps_dir / "s132_nrf52_2.0.1_softdevice.hex")
            self.assertEqual(result.read_text(), ":020000040001F9\n")
            self.assertFalse((dumps_dir / "readme.txt").exists())


if __name__ == "__main__":
    unittest.main()
