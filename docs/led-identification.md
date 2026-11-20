# LED identification

This hardware procedure identifies the blue and green channels connected to
P0.18 and P0.19. It flashes only a temporary local fixture and leaves the
BTHome firmware implementation unchanged.

## Safety gate

Before running the command, verify that both original archive files exist:

- `dumps/full_flash.bin`: 512 KiB
- `dumps/full_uicr.bin`: 4 KiB

The script verifies their SHA-256 values before contacting the ESP32 for
erase or upload work. It does not proceed if either file is missing, has the
wrong size, or has the wrong hash.

## Run the fixture

Build the fixture and inspect P0.18/P0.19:

```bash
python tools/led_identify.py run --host swd.local --delay 2368 --confirm
```

P0.18 pulses first for 1000 ms, then P0.19 pulses separately for 1000 ms.
P0.17 remains off. Repeat the sequence once and enter `blue`, `green`, or
`unknown` for each pin. Use `unknown` if the observation is inconclusive.

Current observation: P0.19 is blue. P0.18 is not yet confirmed.

To save the observation locally:

```bash
python tools/led_identify.py run --host swd.local --delay 2368 --confirm --output led-mapping.json
```

The output file is not a firmware image and is not committed.

## Restore

Restore the original flash and UICR with:

```bash
python tools/led_identify.py restore --host swd.local --confirm
```

The script reports success only after flash and UICR operations are inactive
and no task error remains. If it reports an error or leaves `last_error`
set, retain both dump files and do not claim the original firmware was
restored.
