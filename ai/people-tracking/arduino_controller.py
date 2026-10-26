"""JSON serial bridge. Gas alarm decisions belong to the MCU firmware, never YOLO."""
import json
import math
import threading
import time


def sensor_state(value, observed_at, connected, now=None, stale_after=3.0, danger=False):
    now = time.monotonic() if now is None else now
    if not connected:
        return "disconnected"
    if observed_at is None:
        return "disconnected"
    if now - observed_at > stale_after:
        return "stale"
    if value is None:
        return "disconnected"
    return "danger" if danger else "healthy"


class ClassroomController:
    def __init__(self, port=None, enabled=True, stale_after=3.0, serial_factory=None):
        self.enabled = enabled
        self.port = port
        self.stale_after = stale_after
        self._serial_factory = serial_factory
        self._serial = None
        self._lock = threading.RLock()
        self._write_lock = threading.Lock()
        self._stop = threading.Event()
        self._latest = {}
        self._observed = None
        self._connected = False
        self._last_occupancy = 0.0
        self._thread = None
        if enabled:
            self._thread = threading.Thread(target=self._reader, name="serial-reader", daemon=True)
            self._thread.start()

    def _reader(self):
        while not self._stop.is_set():
            try:
                if self._serial is None:
                    if self._serial_factory is None:
                        import serial
                        from serial.tools import list_ports
                        ports = list(list_ports.comports())
                        # Never choose an arbitrary port when several devices are attached.
                        port = self.port or (ports[0].device if len(ports) == 1 else None)
                        if not port:
                            raise OSError("Set CLASSISENSE_PORT or --port")
                        self._serial = serial.Serial(port, 115200, timeout=0.5, write_timeout=0.5)
                    else:
                        self._serial = self._serial_factory()
                raw = self._serial.readline(2048)
                if raw:
                    self.ingest(json.loads(raw))
            except (ValueError, UnicodeError, TypeError):
                # Malformed data must not refresh the heartbeat.
                continue
            except Exception:
                with self._lock:
                    self._connected = False
                if self._serial:
                    try:
                        self._serial.close()
                    except Exception:
                        pass
                self._serial = None
                self._stop.wait(2)

    def ingest(self, packet, now=None):
        """Validate a versioned full telemetry packet before refreshing freshness."""
        if not isinstance(packet, dict) or packet.get("protocol") != 1:
            raise ValueError("Unsupported MCU protocol; flash firmware/classisense")
        if not isinstance(packet.get("gas_detected"), bool):
            raise ValueError("Missing gas reading")
        if packet.get("gas_state") not in ("healthy", "danger", "disconnected", "stale"):
            raise ValueError("Missing gas state")
        if packet.get("temperature_state") not in ("healthy", "danger", "disconnected", "stale"):
            raise ValueError("Missing temperature state")
        temp = packet.get("temperature_c")
        if temp is not None and (isinstance(temp, bool) or not isinstance(temp, (int, float)) or not math.isfinite(temp) or not -20 <= temp <= 120):
            raise ValueError("Invalid temperature")
        if not isinstance(packet.get("lights_on"), bool) or not isinstance(packet.get("buzzer_on"), bool):
            raise ValueError("Missing actuator state")
        seconds = packet.get("led_on_seconds")
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
            raise ValueError("Invalid LED duration")
        with self._lock:
            self._latest = dict(packet)
            self._observed = time.monotonic() if now is None else now
            self._connected = True

    def update(self, people_count):
        """Occupancy command only. Firmware applies its own lights timer and alarm."""
        now = time.monotonic()
        if self._serial and now - self._last_occupancy >= 1:
            try:
                with self._write_lock:
                    self._serial.write(("OCCUPANCY " + str(max(0, int(people_count))) + "\n").encode())
                self._last_occupancy = now
            except Exception:
                with self._lock:
                    self._connected = False
        return self.get_sensor_data(people_count)

    def get_sensor_data(self, people_count=0, now=None):
        with self._lock:
            packet = dict(self._latest)
            observed = self._observed
            connected = self._connected
        now = time.monotonic() if now is None else now
        gas = packet.get("gas_detected")
        temp = packet.get("temperature_c")
        gas_state = sensor_state(gas, observed, connected, now, self.stale_after, bool(gas))
        temp_state = sensor_state(temp, observed, connected, now, self.stale_after, temp is not None and temp >= 45)
        if gas_state in ("healthy", "danger"):
            gas_state = packet.get("gas_state", "disconnected")
        if temp_state in ("healthy", "danger"):
            temp_state = packet.get("temperature_state", "disconnected")
        return {
            "sampled_at": time.time(),
            "people_count": max(0, int(people_count)),
            "gas_detected": gas if gas_state in ("healthy", "danger") else None,
            "temperature_c": temp if temp_state in ("healthy", "danger") else None,
            "gas_state": gas_state,
            "temperature_state": temp_state,
            "controller_state": sensor_state(True, observed, connected, now, self.stale_after),
            "sensor_age_seconds": None if observed is None else round(max(0, now - observed), 2),
            "lights_on": packet.get("lights_on") if connected and observed is not None and now-observed <= self.stale_after else None,
            "led_on_seconds": packet.get("led_on_seconds"),
            "buzzer_on": packet.get("buzzer_on") if connected and observed is not None and now-observed <= self.stale_after else None,
        }

    def close(self):
        self._stop.set()
        if self._serial:
            self._serial.close()
        if self._thread:
            self._thread.join(timeout=2)
        # Deliberately no alarm-off command: the MCU owns safety, even after disconnect.
