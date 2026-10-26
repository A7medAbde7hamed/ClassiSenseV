# Hardware acceptance checklist

Software simulation does not establish that a real sensor, wiring, power supply or buzzer is functioning. Perform these checks on the physical test setup; record the board, firmware revision, sensor model and results.

1. Upload the sketch to the correct Uno/Nano board; confirm version-1 JSON at 115200 baud.
2. With a safe electrical signal simulator on D4, force LOW and verify the local buzzer turns on. Do not release gas or use flames to test prototype software.
3. Repeat the LOW signal test with the CV program stopped, with the camera unavailable, and with no serial host. The board must remain powered independently; disconnecting its only USB power source stops any firmware.
4. Keep D4 LOW while making the USB transmit buffer unavailable. The alarm loop must continue.
5. Restore HIGH and verify the configured return-to-normal behavior.
6. Disconnect serial data while retaining board power: local alarm remains active and lighting defaults ON after 15 seconds.
7. Send positive occupancy, then zero occupancy for 10 seconds: lighting turns OFF. Stop host commands: lighting returns ON after the heartbeat timeout.
8. Test LM35 at known reference temperatures; compare measurements and verify the configured reference voltage. Test rail/out-of-range faults.
9. Disconnect MCU communications: Python reports disconnected or stale within 3 seconds; the dashboard must never present unknown readings as safe.
10. Disconnect the network, generate test alerts, restart the tracker, restore the network and verify that pending event IDs are delivered without duplicates.

A disconnected gas DO cable cannot be diagnosed by the present digital-only wiring. LM35 cable faults also need appropriate circuitry. Do not mark these cases as physically verified until hardware diagnostics have been added and measured.
