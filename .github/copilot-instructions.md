# Copilot instructions

## Architecture

- The root Python project provides `tools/hardware_test.py`, a command-line client for the ESP32's HTTP API. It reads and writes nRF52 registers to interactively identify board pins; its unit tests are in `tests/test_hardware_test.py`.
- `tools/ESP32_nRF52_SWD` is a Git submodule containing the ESP32 firmware. `src/main.cpp` initializes the SWD, glitcher, and web components; `src/web.cpp` serves the HTTP API and SPIFFS editor; `src/nrf_swd.cpp` handles nRF52 access and queued flash read/write tasks; `src/swd.cpp` implements the SWD transport. The browser UI is in `data/index.htm`.
- The PlatformIO environment settings in `tools/ESP32_nRF52_SWD/platformio.ini` select the board and define hardware pins as build flags. Firmware code consumes these pin macros, so keep pin mappings in sync with the environment configuration.
- `firmware/blinker` is a separate nRF52 PlatformIO project that uses the `nrf52_dk` board profile to compile Arduino firmware for the pilot's nRF52832.
- Factory memory images and their checksum files are stored under `dumps/factory/`.

## Build and test

Run these commands from the repository root:

```bash
uv sync
uv run pytest
uv run pio run --project-dir tools/ESP32_nRF52_SWD -e ESP32_nRF52_SWD
```

Run one test or one test class with pytest selectors:

```bash
uv run pytest tests/test_hardware_test.py::HardwareTestHelpers::test_init_posts_init_command
uv run pytest tests/test_hardware_test.py::HardwareTestHelpers
```

Python tests use `unittest.TestCase` and `unittest.mock`, and are run by pytest. The project has no configured lint command.

## Repository-specific conventions

- Keep the hardware-test client's SWD commands constrained by `ALLOWED_COMMANDS` in `tools/hardware_test.py`; destructive flash operations are deliberately excluded from this interactive pin-mapping tool.
- The ESP32 API is implemented in `src/web.cpp`. Several handlers use HTTP POST with query-string parameters, and many addresses and values are parsed as hexadecimal. Keep the web UI and API parameter names consistent when changing either side.
- The hardware-test client uses the Python standard library (`urllib`) and raises on unexpected API responses; follow this approach rather than adding an HTTP dependency for small API interactions.
- Treat `tools/ESP32_nRF52_SWD` as a submodule: changes to its contents belong to that repository, while this repository records the submodule revision.
- Prefer CLI workflows when a task can be completed equally well from the command line.
- The pilot's nRF52 is accessed through the ESP32 SWD programmer; it is not directly connected or enumerated by PlatformIO as a hardware upload target. For nRF52 work, use PlatformIO to build, then flash through the ESP32/SWD workflow documented in `README.md`; do not assume `pio run -t upload`, a direct nRF52 serial monitor, or an available J-Link.
- After flashing nRF52 firmware through ESP32/SWD, reset the target through the SWD API before hardware verification. Treat a successful flash response (including HTTP 200) as confirmation of the transfer only, not of firmware behavior; mark hardware verification complete only after behavior has been observed on the board or confirmed by the user.
- Keep nRF52 logic testable without hardware where practical. Run pure logic tests on the host and use the ESP32/SWD tools for physical pin and peripheral verification. Check the selected Arduino variant's digital-pin mapping before passing nRF52 P0 pins to Arduino GPIO APIs.

## Documentation and project knowledge

- Keep `README.md` and `TODO.md` current as the code, hardware findings, setup, commands, or workflows change. Update the README with confirmed behavior and instructions; add newly discovered follow-up work to TODO, and mark or remove items when they are completed or no longer relevant.
- At the end of every task, review newly confirmed findings for durable, reusable information that is not already documented, and add it to the appropriate project document without asking for approval. Use `README.md` for confirmed project facts, setup, hardware findings, and workflows; `TODO.md` for open follow-up work; and `copilot-instructions.md` for standing contributor or agent rules. Skip duplicates, one-off or machine-specific details, sensitive information, and unverified assumptions; ask the user if the finding's scope or durability is unclear. Mention documentation updates in the task summary.
- When a problem recurs or its fix is confirmed, record the symptom, verified cause, and working resolution in the relevant README section. If troubleshooting notes grow beyond the README, move them to a dedicated document under `docs/` and link it from the README. Do not leave reusable fixes only in chat history.
- When a user explicitly asks for a tool, workflow, convention, or approach to be consistently used or avoided, apply it and record the standing repository preference here during the same task. Keep these notes actionable and update them if the user changes the preference.
