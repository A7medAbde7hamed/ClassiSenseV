# ClassiSense

**AI-powered classroom monitoring using computer vision, IoT, and Firebase.**

ClassiSense is an academic project exploring how computer vision and connected sensors can be used to monitor classroom occupancy and environmental conditions. The system is intended to count people, track selected sensor readings, control connected indicators/devices, record historical measurements, and surface safety alerts.

> **Project status:** The Python people-tracking component includes a Firebase Cloud Firestore database module. The complete end-to-end hardware setup and dashboard/API integration should be verified against the current code before treating every planned feature as production-ready.

## Current implementation

The repository's `ai/people-tracking/` component uses:

- **Python** for application logic.
- **Ultralytics YOLO**, **OpenCV**, and **NumPy** for computer vision and people tracking.
- **PySerial / PyFirmata2** for supported serial or board communication, depending on the hardware code in use.
- **Firebase Admin SDK** to write monitoring data to **Cloud Firestore**.

The database module currently defines these Firestore destinations:

| Firestore path | Purpose | Fields written by the current module |
| --- | --- | --- |
| `classroom/live_status` | Latest classroom state, updated no more often than every 2 seconds | `people_count`, `led_is_on`, `led_on_seconds`, `temperature_c`, `gas_detected`, `gas_danger`, `updated_at` |
| `monitoring_logs` | Periodic history, nominally every 180 seconds | `people_count`, `led_is_on`, `led_on_seconds`, `temperature_c`, `gas_detected`, `created_at` |
| `alerts` | Safety alert records | `alert_type`, `severity`, `measured_value`, `created_at` |

The current alert logic records a gas-leak alert when the gas-danger input is active and a high-temperature alert when the temperature is at least **45 °C**. Repeated alerts of the same type are rate-limited by a 60-second cooldown. These values are application logic, not a substitute for certified safety equipment.

## Architecture

The intended data flow is:

```text
Camera
  |
  v
Python computer-vision / people-tracking application <--> IoT controller and sensors
  |
  v
Firebase Admin SDK
  |
  v
Cloud Firestore
  |
  v
Dashboard / data analysis (integration to be verified)
```

The Python process uses the Firebase Admin SDK to write to Firestore. Firebase does **not** automatically host or run the Python computer-vision process; that process must run on a suitable computer/device or on separately configured compute infrastructure.

## Getting started

### 1. Requirements

- Python version compatible with the installed project dependencies.
- A camera and any supported hardware required by the people-tracking application.
- A Firebase project with **Cloud Firestore** enabled.
- A Firebase service-account credential for the Python Admin SDK.

### 2. Install Python dependencies

From the repository root:

```bash
python -m pip install -r ai/people-tracking/requirements.txt
```

### 3. Configure Firebase credentials

1. Create or select a Firebase project and enable Cloud Firestore.
2. Generate a service-account key only if your deployment environment requires a downloaded key.
3. Place the credential file at:

   `ai/people-tracking/serviceAccountKey.json`

4. Keep this file private. **Never commit service-account keys or paste them into issues, pull requests, screenshots, or public messages.** The repository ignore rules are intended to exclude the key file.
5. Run the Python application using its existing entry point and configuration for your hardware.

The database module looks for the key relative to `ai/people-tracking/database.py`. If it cannot find the key, it logs an error and Firestore writes will not be available.

### 4. Verify Firestore writes

When the application runs with valid credentials and calls the database manager, verify that:

- `classroom/live_status` is updated with the latest available readings.
- `monitoring_logs` receives periodic records.
- `alerts` receives records when the configured alert conditions are met.

The precise run command depends on the computer-vision entry point in the current branch; consult the Python files in `ai/people-tracking/` rather than assuming a command that may not match the repository.

## Security notes

- Treat Firebase service-account credentials as secrets.
- The Admin SDK runs with privileged server-side access; do not put its service-account key in browser/frontend code.
- If a web dashboard reads Firestore directly, configure and test Firestore Security Rules and authentication for that client. Do not rely on hiding a database URL or project ID as access control.
- Keep local safety actions independent of dashboard availability where the hardware design supports this.

Official Firebase documentation:
- [Set up the Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)
- [Get started with Cloud Firestore Security Rules](https://firebase.google.com/docs/firestore/security/get-started)

## Development notes

- The root README should describe implemented behavior separately from planned features.
- Before deploying, test the camera pipeline, sensor/controller communication, Firestore writes, alert thresholds, and failure behavior with the actual hardware.
- Check whether any remaining MySQL dependency or configuration is still used elsewhere before removing it.

## Future work

Potential next steps, subject to the team's implementation plan:

- Complete and document the dashboard integration.
- Add setup instructions for each supported board and sensor configuration.
- Add tests for Firestore writes, missing credentials, connection failures, and alert cooldowns.
- Document deployment, authentication, data retention, and access-control policies.
- Validate the full camera/sensor-to-Firestore-to-dashboard flow.

## Contributing

Use feature branches and open a pull request for review before merging changes into `main`. Keep secrets and hardware-specific local configuration out of commits.
