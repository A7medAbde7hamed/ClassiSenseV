# Verification · 2026-10-26

## Confirmed

- Python: 21 passing tests covering missing/stale sensors, malformed telemetry, network retry, restart persistence, idempotent IDs, blocked-network independence, capture failure, bounded EOF retry, and cleanup after inference failure.
- Node: 10 passing tests covering authentication, CSRF, Firestore data decoding/query boundaries, failure propagation, setup mode, and actual service-worker offline fallback/cache exclusion behavior.
- Native C++ firmware simulation: autonomous gas alarm without serial host or available transmit space; lighting timeout; ADC fault; versioned telemetry.
- Actual Arduino Uno cross-compile: Arduino AVR core 1.8.8, 7,624 bytes program storage (23%), 773 bytes globals (37% of 2,048-byte RAM).
- GitHub Actions run 40346746287: both software checks and Uno compile completed successfully on the first implementation commit.
- Vercel build: initial deployment READY; build command passed; monitoring API returned 200 setup state, no-store, and no fabricated live readings.
- Browser: overview, history expansion (30 → 60 rows), gas-only alert filtering, devices, settings, and switching between demo and disconnected live mode verified.
- Video: two real 120-frame CPU runs; raw results and small-sample count evaluation are committed separately.

## Requires user hardware / credentials

- No Firebase service account was supplied. Real Firestore reads/writes and the hardware-to-cloud-to-browser path have not been tested against a real Firebase project. Tests use controlled fakes; demo data remains explicitly labelled.
- No physical Arduino, MQ-5 or LM35 was attached. Upload firmware and perform the hardware acceptance checklist. A successful cross-compile/simulation does not verify electrical behavior.
- Digital MQ-5 cable disconnection and floating LM35 cable faults cannot be reliably diagnosed by the present hardware.
- The five annotated frames are a calibration sample from one clip, not a representative accuracy benchmark. Exact counts still need improvement.
