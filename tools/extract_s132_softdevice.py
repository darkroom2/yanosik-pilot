"""Download the Nordic S132 2.0.1 package and extract only its SoftDevice HEX file."""

from pathlib import Path
from io import BytesIO
import shutil
from urllib.request import urlopen
import zipfile


URL = (
    "https://nsscprodmedia.blob.core.windows.net/prod/software-and-other-downloads/"
    "softdevices/s132/s132nrf52201.zip"
)
HEX_NAME = "s132_nrf52_2.0.1_softdevice.hex"


def download_zip() -> bytes:
    with urlopen(URL) as response:
        return response.read()


def extract_hex(zip_bytes: bytes, dumps_dir: Path) -> Path:
    destination = dumps_dir / HEX_NAME
    dumps_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(BytesIO(zip_bytes)) as archive:
        matches = [
            name
            for name in archive.namelist()
            if Path(name).name == HEX_NAME
        ]
        if len(matches) != 1:
            raise FileNotFoundError(
                f"Expected exactly one {HEX_NAME} in ZIP, found {len(matches)}"
            )

        with archive.open(matches[0]) as source, destination.open("wb") as output:
            shutil.copyfileobj(source, output)

    return destination


def main() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    dumps_dir = repository_root / "dumps"

    print(f"Pobieranie {URL}")
    destination = extract_hex(download_zip(), dumps_dir)
    print(destination)


if __name__ == "__main__":
    main()
