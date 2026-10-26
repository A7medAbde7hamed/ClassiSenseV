# Local ClassiSense processor

See the repository [README](../../README.md) for setup, pinned dependencies, current firmware and Firebase configuration.

The current runner uses YOLO26 nano and ByteTrack. It counts visible people in the complete frame; interactive ROI selection and spacebar pause are not implemented. Run `python tracker.py --help` for supported options.

**Flash `firmware/classisense/classisense.ino` first. StandardFirmata is no longer the serial protocol.**
