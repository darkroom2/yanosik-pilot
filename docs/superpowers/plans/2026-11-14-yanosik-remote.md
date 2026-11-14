# Yanosik BTHome Remote Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare and verify nRF52832 BTHome remote firmware and a backup-first operator guide, without flashing hardware.

**Architecture:** Keep button recognition, BTHome serialization, and the bounded transmission queue independent of hardware for host testing. A thin PlatformIO BLE/GPIO adapter connects those components to the remote; upstream ESP32 SWD tooling remains separate.

**Tech Stack:** C++ for firmware and host tests, PlatformIO Nordic nRF52, an nRF52832-compatible BLE framework selected after checking its build artifacts.

**Spec:** [Approved design](../specs/2026-11-14-yanosik-remote-design.md).

## Global Constraints

- Do not flash, erase, recover, unlock or test LEDs on hardware in this phase.
- No destructive future operation before a verified full backup and a documented way to restore all required state, plus separate user authorization.
- P0.13/P0.14 are active-low pull-up buttons; P0.17/P0.18/P0.19 are active-low LEDs.
- Both buttons support single, double and long press; startup distinguishes P0.18 from P0.19 without assigning unverified colors.
- BTHome v2 advertisements are trigger-based and unencrypted; use stable identity, two consistently ordered button objects and packet IDs.
- Queue eight pending events and visibly signal overflow; no guarantee of BLE delivery.
- Hardware variant, available memory and low-frequency clock are not yet confirmed. No claim of tested restoration or measured power consumption.
- Never commit backups, credentials, or downloaded third-party source.

## Review Focus

1. Repeated reads may be identical but incomplete: the guide must require full flash, UICR and a documented restoration method, and identify unsupported regions.
2. The second button must not be interpreted as the first: test both ordered objects in every packet.
3. A retransmitted event must not fire repeatedly: test identical packet IDs for retransmits and new IDs for distinct events.
4. A held button, switch bounce, or concurrent presses must not create spurious gestures: cover each with timestamped tests.
5. A full transmission queue or a BLE error must not silently discard events: test overflow reporting and error handling.

---

### Task 1: Verify build strategy and preservation procedure

**Files:**
- Create: `platformio.ini`
- Create: `README.md`
- Create: `src/main.cpp`

**Interfaces:** Produces a named PlatformIO environment for the selected nRF52832 BLE stack and a documented build command and image layout.

- [ ] Inspect PlatformIO's supported nRF52832 board definitions, framework configuration, BLE stack and linker/image generation; choose a reproducible versioned configuration. Confirm that a software low-frequency clock can be selected. If the stack cannot produce an image including its required BLE stack, resolve that before proceeding.
- [ ] Configure the target explicitly as an assumption, using a minimal compilable BLE application. Record flash and RAM assumptions, low-frequency clock source, image addresses, required stack, and the actual generated BIN/HEX files in `README.md`.
- [ ] Run `pio run -e <chosen-environment>` and inspect the image and linker output. Expected: a successful build, a documented complete programming image and no memory overflow. If PlatformIO is missing, install it only after the build command demonstrates that failure.
- [ ] Inspect the upstream ESP32 SWD implementation and document exact supported non-destructive flash/UICR reads and restore operations, or explicitly mark them unsupported. Document checksums, repeated reads, backup storage outside Git, wiring, Wi-Fi secrets, recovery erase risk, and the requirement to stop if a full backup or restore method is unavailable.
- [ ] Document that ordinary SWD requires no glitch circuit and that protected-readout glitching is outside this phase. Do not prescribe recovery as a way to obtain a backup.

### Task 2: Button gesture recognition

**Files:**
- Create: `include/buttons.h`
- Create: `src/buttons.cpp`
- Create: `test/test_buttons/test_main.cpp`

**Interfaces:**
- Produces `enum class Gesture { Single, Double, Long };`, `struct ButtonEvent { uint8_t button; Gesture gesture; };`, and `ButtonRecognizer::update(uint8_t button, bool pressed, uint32_t now_ms)` returning any emitted event through a non-allocating result type.
- Button indices are `0` and `1`; `pressed` already represents active-low hardware input.

- [ ] Write host tests using 30 ms debounce, a 350 ms double-click window and an 800 ms long-press threshold. Assert single emits only after the double window; two short presses emit one double; a hold emits one long and no single on release.
- [ ] Add cases for bounce, exact timing boundaries, timer wraparound, independent simultaneous presses and a second press held long. Define and test that the first completed short press is emitted separately before the second long gesture.
- [ ] Run the configured host test command and confirm the new tests fail because the recognizer is missing.
- [ ] Implement `ButtonRecognizer`, independently tracking both buttons without dynamic allocation. Emit events only after debounced transitions; use wrap-safe unsigned elapsed-time arithmetic.
- [ ] Run the host tests again; all gesture tests must pass.

### Task 3: BTHome packets and transmission queue

**Files:**
- Create: `include/bthome.h`
- Create: `src/bthome.cpp`
- Create: `test/test_bthome/test_main.cpp`

**Interfaces:**
- Consumes `ButtonEvent` and `Gesture` from Task 2.
- Produces `make_bthome_payload(ButtonEvent event, uint8_t packet_id)` as a fixed-size byte array and `EventQueue` with non-allocating `push(ButtonEvent)` and `pop()` operations; `push` reports failure when eight pending items are present.
- Encodes packet ID object `0x00`, then both button objects `0x3A` in fixed button order; inactive button value is `0x00`. Gesture values are `0x01`, `0x02`, and `0x04`.

- [ ] Write exact-byte tests for both buttons and all three gestures: the BTHome service data begins `D2 FC 44 00 <packet-id> 3A <button-0> 3A <button-1>`. Test packet-ID wrap from `255` to `0`, retransmission with the same ID, and a distinct ID for each new event.
- [ ] Write FIFO tests for eight queued events, ninth-event rejection without overwriting existing entries, and a subsequent successful enqueue after a dequeue.
- [ ] Run the host test command and confirm these tests fail because the serializer and queue are missing.
- [ ] Implement the serializer and queue. Assign the packet ID once when beginning a queued event, not per transmission.
- [ ] Run all host tests; the exact-byte and FIFO cases must pass.

### Task 4: Hardware adapter and build verification

**Files:**
- Modify: `src/main.cpp`
- Modify: `platformio.ini`
- Create: `include/remote.h`
- Create: `src/remote.cpp`
- Create: `test/test_remote/test_main.cpp`

**Interfaces:**
- Consumes `ButtonRecognizer`, `ButtonEvent`, `make_bthome_payload`, and `EventQueue`.
- Produces an adapter-independent remote controller whose inputs are button states and time and whose outputs request advertisement and LED state changes; define its concrete signature before implementation in `include/remote.h`.

- [ ] Write host tests for two simultaneous gesture streams, ordered queued advertisements, reuse of the same ID for repeats, red LED indication on overflow, and an explicit error indication when the BLE adapter rejects an advertisement.
- [ ] Run the host tests and confirm failure before implementing the controller.
- [ ] Integrate nonblocking gesture polling, a bounded event queue, BLE advertising with the required flags and BTHome service data, and a stable identity. Document advertisement interval, retransmission duration and how startup discovery works. Do not block button processing during transmissions or LED sequences.
- [ ] Initialize LEDs safely off before driving them as outputs; at startup illuminate P0.18 and then P0.19 individually. Give documented red LED event feedback and a distinguishable overflow/error signal.
- [ ] Run all host tests, then `pio run -e <chosen-environment>`. Verify the complete image and memory report again. Do not invoke any upload target.

### Task 5: Operator guide and final validation

**Files:**
- Modify: `README.md`

**Interfaces:** Consumes the actual build outputs, programmer capabilities and behavior established by Tasks 1–4.

- [ ] Document Windows/VS Code PlatformIO build commands, image paths and programmer setup without embedding credentials. Include a backup and restoration checklist that stops on read-protection, unsupported UICR handling, incomplete backup or missing restoration capability.
- [ ] Describe a separately authorized future flashing procedure only where the verified programmer supports it; otherwise explicitly identify the blocker. Include a hardware checklist for LED color mapping, all six gestures, discovery, reception and eventual restoration, without claiming they were performed.
- [ ] Explain Home Assistant button identification, gesture timing, event buffering, unencrypted/spoofable BLE, and the limits of battery-life and delivery claims.
- [ ] Run all configured host tests and the build command. Report actual results and hardware-dependent unknowns; do not claim hardware validation.

## Execution notes

Work in the existing workspace unless the user specifically requests isolation. Do not create commits without the user's request. If verified build or programmer capabilities contradict the design, stop and report the constraint rather than weakening the preservation gate.
