# Yanosik BTHome remote design

## Purpose and scope

Prepare firmware and instructions to turn the existing two-button nRF52832
remote into a Home Assistant controller using BTHome v2. Retaining the
ability to restore the original firmware is essential. This phase prepares
and tests software only: it does not flash either device or operate on the
remote.

The repository currently contains the idea and no firmware. Hardware
details and pin assignments are as specified in `IDEA.md`, not independently
verified.

## Approaches

1. **Recommended: PlatformIO firmware with BTHome BLE advertisements,
   using the existing ESP32 SWD project for programming.** This leverages
   Home Assistant's BTHome support and avoids implementing a programmer.
2. A custom Home Assistant integration and proprietary BLE protocol would
   add maintenance and is unnecessary for standard button events.
3. Building a new SWD programmer would duplicate an existing tool and add
   risk to the backup and restoration workflow.

The user selected standard single, double and long presses for both buttons
and requested preparation without flashing.

## Preservation gate

No erase, recovery, unlock, programming, or first-boot LED test on the
remote until a complete original backup is read and verified and the user
separately authorizes the operation. Capture flash and UICR, device identity,
memory size, tool versions and any other restorable configuration supported
by the programmer. Verify independent repeated reads and checksums; document
what cannot be read or restored. Store backups outside version control.
Matching reads alone do not prove a successful restoration; actual restoration
remains unverified until tested. Block destructive operations unless a
documented method can restore all required captured state.

If read protection prevents backup, stop before destructive operations.
Nordic recovery erases user code and UICR. The ESP32 project's optional
glitching method requires additional hardware and is not guaranteed to work
or preserve the device; it is not part of this phase. Do not promise that
the original state is recoverable when protection blocks readout or when
device-specific data cannot be captured.

## Remote firmware

- Use PlatformIO's nRF52 support, selecting and documenting a compatible BLE
  stack and board configuration for the actual nRF52832 variant. Do not
  assume an existing bootloader, SoftDevice, low-frequency crystal, or a
  particular flash capacity without verifying the build assumptions. Produce
  a complete flashable image, including any required BLE stack, with the
  supported programmer format documented. The build target is conditional:
  confirm the actual chip variant, memory and clock configuration before
  any future flashing.
- Buttons P0.13 and P0.14 are active-low inputs with pull-ups. Debounce them
  independently. Each produces single press, double press and long press;
  document thresholds and ensure one gesture does not emit conflicting
  events. Simultaneous buttons are processed independently.
- Advertise BTHome v2 trigger-based, unencrypted events, using a stable BLE
  identity, flags, packet IDs and two consistently ordered button objects so
  Home Assistant can distinguish the buttons and deduplicate retransmissions.
  Repeat each event briefly for reception. Queue up to eight pending events
  while transmitting; on overflow, signal an error with the red LED and
  document that the new event was dropped. BLE delivery is not guaranteed.
  Idle behavior should conserve battery; exact power consumption and
  reception reliability require hardware measurement.
- P0.17, P0.18 and P0.19 are active-low LED outputs. At each startup, briefly
  illuminate P0.18 and then P0.19 separately so the user can observe the
  colors; do not claim a color mapping before observation. Provide brief
  nonblocking event feedback, with the signal documented independently of
  the unknown blue/green mapping.
- Document that unencrypted advertisements are observable and can be spoofed;
  this controller is not suitable for security-critical actions.

## Programmer and operator guidance

Document how to build and configure the upstream
[ESP32_nRF52_SWD](https://github.com/atc1441/ESP32_nRF52_SWD) project,
including its web interface, Wi-Fi setup, SWD wiring and known limitations.
Avoid committing Wi-Fi credentials. Distinguish ordinary SWD wiring from the
additional, out-of-scope glitching circuitry. Provide a backup-first checklist,
and only describe later flashing and restoration for operations that the
chosen programmer and image format actually support; explicitly flag any
unsupported UICR backup or restore. Never imply that merely connecting the
ESP32 makes a destructive operation safe.

## Verification and acceptance

- Automated host-side tests exercise debounce, gesture timing boundaries,
  concurrent buttons, and the exact BTHome payload, button ordering and
  packet-ID behavior.
- Build the nRF52832 firmware with PlatformIO and verify the produced image
  contains its required BLE stack and fits the assumed device memory.
- Document a separate hardware acceptance checklist: independently verify
  backup, LED mapping, all six gestures, Home Assistant discovery and event
  delivery, and, only with explicit authorization and adequate backup,
  restoration. These hardware checks are not claimed as completed.
- No source code, credentials or firmware dumps are sent to third-party
  services. External dependencies are limited to those required to build.

## References

- [BTHome v2 format](https://bthome.io/format/)
- [PlatformIO Nordic nRF52 platform](https://docs.platformio.org/en/latest/platforms/nordicnrf52.html)
- [Nordic APPROTECT and recovery](https://devzone.nordicsemi.com/nordic/nordic-blog/b/blog/posts/working-with-the-nrf52-series-improved-approtect)
- [ESP32 nRF52 SWD programmer](https://github.com/atc1441/ESP32_nRF52_SWD)
