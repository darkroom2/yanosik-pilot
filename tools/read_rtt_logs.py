import argparse
import base64
import re
import struct
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


RAM_ADDRESS = 0x20000000
RAM_SIZE = 0x10000
RTT_MAGIC = b"SEGGER RTT"


def extract_ring(ram, ram_address, buffer_address,
                 buffer_size, read_offset, write_offset):
    relative = buffer_address - ram_address
    if relative < 0 or relative + buffer_size > len(ram):
        return b""
    start = relative
    length = (write_offset - read_offset + buffer_size) % buffer_size
    if length == 0:
        return b""
    output = bytearray()
    for index in range(length):
        output.append(ram[start + ((read_offset + index) % buffer_size)])
    return bytes(output)


def clean_rtt_log(raw):
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)
    text = text.replace("\x00", "")
    return text.replace("\r", "")


def find_control_block(ram):
    index = ram.find(RTT_MAGIC)
    if index < 0:
        return None
    if index % 4:
        return index - (index % 4)
    return index


def read_rtt_up_buffer(ram):
    control = find_control_block(ram)
    if control is None:
        raise RuntimeError("SEGGER RTT control block not found in RAM dump")
    if control + 32 > len(ram):
        raise RuntimeError("Incomplete SEGGER RTT control block")

    max_up = struct.unpack_from("<I", ram, control + 16)[0]
    if max_up < 1:
        raise RuntimeError("SEGGER RTT has no up channels")

    descriptor = control + 24
    name_address, buffer_address, buffer_size, write_offset, read_offset = (
        struct.unpack_from("<IIIII", ram, descriptor)
    )

    return extract_ring(
        ram,
        RAM_ADDRESS,
        buffer_address,
        buffer_size,
        read_offset,
        write_offset,
    )


class SwdClient:
    def __init__(self, host, username, password):
        self.base_url = host.rstrip("/")
        self.auth = "Basic " + base64.b64encode(
            f"{username}:{password}".encode()
        ).decode()

    def request(self, method, path, output_path=None):
        request = Request(self.base_url + path, method=method)
        request.add_header("Authorization", self.auth)
        with urlopen(request, timeout=60) as response:
            if output_path:
                Path(output_path).write_bytes(response.read())
                return
            return response.read().decode("utf-8", errors="replace")

    def download_bytes(self, path):
        request = Request(self.base_url + path, method="GET")
        request.add_header("Authorization", self.auth)
        with urlopen(request, timeout=60) as response:
            return response.read()

    def wait_finished(self, timeout):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            state = self.request("GET", "/get_state?cmd=0")
            if "no task running" in state.lower():
                return
            time.sleep(1)
        raise TimeoutError("RAM dump task did not finish")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Dump nRF52 RAM and print the SEGGER RTT up-channel log"
    )
    parser.add_argument("--host", default="http://swd.local")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin")
    parser.add_argument("--ram-address", default="20000000")
    parser.add_argument("--ram-size", default="10000")
    parser.add_argument("--log", default="rtt.log")
    parser.add_argument("--timeout", type=int, default=180)
    return parser.parse_args()


def main():
    args = parse_args()
    ram_address = int(args.ram_address, 16)
    ram_size = int(args.ram_size, 16)
    client = SwdClient(args.host, args.username, args.password)

    params = urlencode({
        "cmd": "dump_flash",
        "file": "ram.bin",
        "offset": f"{ram_address:x}",
        "size": f"{ram_size:x}",
    })
    print(client.request("POST", "/flash_cmd?" + params))
    client.wait_finished(args.timeout)

    ram = client.download_bytes("/edit?download=ram.bin")
    log = read_rtt_up_buffer(ram)
    cleaned_log = clean_rtt_log(log)
    Path(args.log).write_text(cleaned_log, encoding="utf-8")
    print(cleaned_log, end="")


if __name__ == "__main__":
    main()
