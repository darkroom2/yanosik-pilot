import argparse
import json
import sys
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen


P0_BASE = 0x50000000
P0_OUT = P0_BASE + 0x508
P0_OUTSET = P0_BASE + 0x508
P0_OUTCLR = P0_BASE + 0x50C
P0_IN = P0_BASE + 0x510
P0_DIRSET = P0_BASE + 0x518
P0_PIN_CNF13 = P0_BASE + 0x734
P0_PIN_CNF14 = P0_BASE + 0x738

ALLOWED_COMMANDS = {
    "init",
    "read_register",
    "write_register",
    "get_state",
}


def led_on_mask(pin):
    return 1 << pin


def led_off_mask(pin):
    return 1 << pin


def input_bit(value, pin):
    return (value >> pin) & 1


def parse_buzzer_pins(value):
    pins = []
    for item in value.split(","):
        item = item.strip()
        if not item.isdigit():
            raise ValueError("Buzzer pin list must contain decimal GPIO numbers")
        pin = int(item)
        if pin < 0 or pin > 31:
            raise ValueError("Buzzer GPIO pin must be in the range 0..31")
        pins.append(pin)
    if not pins:
        raise ValueError("Buzzer pin list cannot be empty")
    return pins


def swd_post(host, params):
    command = params.get("cmd")
    if command not in ALLOWED_COMMANDS:
        raise ValueError("Destructive or unsupported SWD command rejected")
    url = host.rstrip("/") + "/set_swd?" + urlencode(params)
    request = Request(url, method="POST")
    with urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8", errors="replace")


def swd_read(host, address):
    text = swd_post(host, {"cmd": "read_register", "address": f"{address:X}"})
    marker = " value: "
    if marker not in text:
        raise RuntimeError("Unexpected register response: " + text)
    return int(text.rsplit(marker, 1)[1].strip(), 16)


def swd_write(host, address, value):
    swd_post(host, {
        "cmd": "write_register",
        "address": f"{address:X}",
        "value": f"{value:X}",
    })


def swd_init(host):
    try:
        swd_post(host, {"cmd": "init"})
        return True
    except Exception as exc:
        raise RuntimeError("Cannot initialize SWD: " + str(exc)) from exc


def wait_for_user(prompt):
    answer = input(prompt + " [y/n/u]: ").strip().lower()
    if answer in ("y", "yes"):
        return "yes"
    if answer in ("n", "no"):
        return "no"
    return "unknown"


def test_leds(host, duration):
    results = {}
    swd_write(host, P0_DIRSET, (1 << 17) | (1 << 18) | (1 << 19))

    swd_write(host, P0_OUTCLR, 1 << 17)
    time.sleep(duration)
    swd_write(host, P0_OUTSET, 1 << 17)
    results["red_P0_17"] = wait_for_user("Did the red LED light on P0.17?")

    mask = (1 << 18) | (1 << 19)
    swd_write(host, P0_OUTCLR, mask)
    time.sleep(duration)
    results["green_blue_both"] = wait_for_user("Did both P0.18 and P0.19 LEDs light?")

    swd_write(host, P0_OUTSET, mask)
    swd_write(host, P0_OUTCLR, 1 << 18)
    time.sleep(duration)
    results["P0_18_green"] = wait_for_user("Did P0.18 light as green?")

    swd_write(host, P0_OUTSET, 1 << 18)
    swd_write(host, P0_OUTCLR, 1 << 19)
    time.sleep(duration)
    results["P0_19_blue"] = wait_for_user("Did P0.19 light as blue?")
    swd_write(host, P0_OUTSET, 1 << 19)
    return results


def test_buttons(host):
    swd_write(host, P0_PIN_CNF13, 0x0C)
    swd_write(host, P0_PIN_CNF14, 0x0C)
    time.sleep(0.1)

    released = swd_read(host, P0_IN)
    print(f"P0 IN with both released: 0x{released:08X}")
    bit13_released = input_bit(released, 13)
    bit14_released = input_bit(released, 14)

    print("Press and hold button #1 (P0.13 / Pin 16), then press Enter.")
    input()
    held1 = swd_read(host, P0_IN)
    print(f"P0 IN with button #1 held: 0x{held1:08X}")

    print("Release button #1 and press and hold button #2 (P0.14 / Pin 17), then press Enter.")
    input()
    held2 = swd_read(host, P0_IN)
    print(f"P0 IN with button #2 held: 0x{held2:08X}")

    return {
        "P0_13_released": bit13_released,
        "P0_14_released": bit14_released,
        "P0_13_held": input_bit(held1, 13),
        "P0_14_held": input_bit(held2, 14),
        "P0_13_bit_mask": 1 << 13,
        "P0_14_bit_mask": 1 << 14,
        "raw_released": f"0x{released:08X}",
        "raw_button1": f"0x{held1:08X}",
        "raw_button2": f"0x{held2:08X}",
    }


def test_buzzer_pins(host, pins, duration):
    results = {}
    for pin in pins:
        bit = 1 << pin
        swd_write(host, P0_DIRSET, bit)
        swd_write(host, P0_OUTSET, bit)
        cycles = max(5, int(duration * 500))
        period = duration / cycles
        for _ in range(cycles):
            swd_write(host, P0_OUTCLR, bit)
            time.sleep(period / 2)
            swd_write(host, P0_OUTSET, bit)
            time.sleep(period / 2)
        swd_write(host, P0_OUTSET, bit)
        results[f"P0_{pin}"] = wait_for_user(f"Did P0.{pin} make the buzzer react?")
    return results


def build_parser():
    parser = argparse.ArgumentParser(description="Interactive nRF52832 hardware mapping tests")
    parser.add_argument("--host", default="http://swd.local")
    parser.add_argument("--duration", type=float, default=0.5)
    parser.add_argument("--buzzer-pins", default="15,16,20,24,25,31")
    parser.add_argument("--led-only", action="store_true")
    parser.add_argument("--button-only", action="store_true")
    parser.add_argument("--buzzer-only", action="store_true")
    parser.add_argument("--output")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.duration <= 0:
        print("Error: --duration must be greater than zero", file=sys.stderr)
        return 2

    try:
        buzzer_pins = parse_buzzer_pins(args.buzzer_pins)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    modes = sum((args.led_only, args.button_only, args.buzzer_only))
    if modes > 1:
        print("Error: choose only one of --led-only, --button-only, --buzzer-only", file=sys.stderr)
        return 2

    report = {"host": args.host, "tests": {}}
    try:
        swd_init(args.host)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not args.button_only and not args.buzzer_only:
        report["tests"]["leds"] = test_leds(args.host, args.duration)
    if not args.led_only and not args.buzzer_only:
        report["tests"]["buttons"] = test_buttons(args.host)
    if not args.led_only and not args.button_only:
        report["tests"]["buzzers"] = test_buzzer_pins(
            args.host, buzzer_pins, args.duration
        )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as output:
            json.dump(report, output, indent=2)
        print(f"Saved results to {args.output}")
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
