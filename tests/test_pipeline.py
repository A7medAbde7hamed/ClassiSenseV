import importlib.util
from pathlib import Path
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'ai'/'people-tracking'))
sys.path.insert(0,str(ROOT/'tools'))
from arduino_controller import ClassroomController, sensor_state
from database import DatabaseManager, Outbox
from tracker import capture_source
from evaluate_counts import evaluate


def packet(**kwargs):
    return dict(protocol=1,gas_detected=False,gas_state='healthy',temperature_c=25.,temperature_state='healthy',lights_on=True,buzzer_on=False,led_on_seconds=12,**kwargs)


class SensorTests(unittest.TestCase):
    def setUp(self): self.controller=ClassroomController(enabled=False)
    def tearDown(self): self.controller.close()
    def test_missing_reading_is_never_safe(self):
        data=self.controller.get_sensor_data(now=10)
        self.assertEqual(data['gas_state'],'disconnected')
        self.assertIsNone(data['gas_detected'])
    def test_heartbeat_becomes_stale(self):
        self.controller.ingest(packet(),now=10)
        self.assertEqual(self.controller.get_sensor_data(now=11)['gas_state'],'healthy')
        data=self.controller.get_sensor_data(now=14)
        self.assertEqual(data['gas_state'],'stale')
        self.assertIsNone(data['temperature_c'])
        self.assertIsNone(data['buzzer_on'])
    def test_fresh_danger_and_mcu_disconnection(self):
        p=packet();p.update(gas_detected=True,gas_state='danger',temperature_state='disconnected',temperature_c=None)
        self.controller.ingest(p,now=10)
        data=self.controller.get_sensor_data(now=11)
        self.assertEqual(data['gas_state'],'danger')
        self.assertEqual(data['temperature_state'],'disconnected')
    def test_malformed_packet_does_not_refresh_freshness(self):
        self.controller.ingest(packet(),now=10)
        with self.assertRaises(ValueError):self.controller.ingest({'protocol':1},now=12)
        self.assertEqual(self.controller.get_sensor_data(now=14)['gas_state'],'stale')
    def test_nan_temperature_rejected(self):
        p=packet();p['temperature_c']=float('nan')
        with self.assertRaises(ValueError):self.controller.ingest(p)
    def test_serial_disconnect_state(self):
        self.controller.ingest(packet(),now=10);self.controller._connected=False
        self.assertEqual(self.controller.get_sensor_data(now=11)['gas_state'],'disconnected')
    def test_warmup_does_not_hide_actuator(self):
        p=packet();p['gas_state']='stale';self.controller.ingest(p,now=10)
        self.assertTrue(self.controller.get_sensor_data(now=11)['lights_on'])


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'outbox.sqlite3'
    def tearDown(self):self.temp.cleanup()
    def test_pending_jobs_survive_restart(self):
        box=Outbox(self.path);key=box.enqueue('alert',{'sampled_at':100});box.close()
        box=Outbox(self.path);self.assertEqual(box.next()[0],key);box.close()
    def test_live_status_coalesces_without_losing_alerts(self):
        box=Outbox(self.path);box.enqueue('alert',{'v':1});box.enqueue('live',{'v':1});box.enqueue('live',{'v':2})
        self.assertEqual(box.count(),2);self.assertEqual(box.next()[1],'alert');box.close()
    def test_network_failure_retries_same_event_id(self):
        calls=[]
        def sink(kind,key,data):
            calls.append(key)
            if len(calls)==1:raise OSError('offline')
        manager=DatabaseManager(self.path,sink=sink,start_worker=False)
        manager.outbox.enqueue('alert',{'sampled_at':10})
        manager.process_once(now=100);self.assertEqual(manager.outbox.count(),1)
        self.assertFalse(manager.process_once(now=100.5))
        manager.process_once(now=102);self.assertEqual(manager.outbox.count(),0)
        self.assertEqual(calls[0],calls[1]);manager.close()
    def test_failed_enqueue_does_not_advance_timers(self):
        manager=DatabaseManager(self.path,start_worker=False)
        def fail(*_):raise OSError('disk full')
        manager.outbox.enqueue=fail
        with self.assertRaises(OSError):manager.publish({'sampled_at':1},now=10)
        self.assertIsNone(manager.last_live);manager.close()
    def test_first_hazard_is_queued_immediately(self):
        manager=DatabaseManager(self.path,start_worker=False)
        manager.publish({'sampled_at':10,'gas_state':'danger'},now=0)
        self.assertEqual(manager.outbox.next()[1],'alert');manager.close()
    def test_enqueue_is_independent_of_blocking_network(self):
        import threading
        entered=threading.Event();release=threading.Event()
        def sink(*_):entered.set();release.wait(2)
        manager=DatabaseManager(self.path,sink=sink)
        try:
            manager.publish({'sampled_at':10},now=10);self.assertTrue(entered.wait(1))
            start=time.perf_counter();manager.publish({'sampled_at':12,'gas_state':'danger'},now=12)
            self.assertLess(time.perf_counter()-start,.1)
        finally:release.set();manager.close()
    def test_retry_does_not_block_new_alert(self):
        box=Outbox(self.path);a=box.enqueue('log',{});box.fail(a,0,now=100);b=box.enqueue('alert',{})
        self.assertEqual(box.next(now=100)[0],b);box.close()


class MetricsTests(unittest.TestCase):
    def test_paths_are_independent_of_working_directory(self):
        self.assertEqual(capture_source('0'),0)
        self.assertEqual(capture_source('ai/people-tracking/video.mp4'),str(ROOT/'ai/people-tracking/video.mp4'))
    def test_count_error_metrics(self):
        result=evaluate([dict(frame=0,people_count=3,fps=20,inference_ms=40),dict(frame=1,people_count=5,fps=22,inference_ms=42)],[dict(frame=0,people_count=2),dict(frame=1,people_count=5)])
        self.assertEqual(result['mae_people'],.5);self.assertEqual(result['exact_count_rate'],.5)
    def test_no_ground_truth_is_not_accuracy(self):
        with self.assertRaises(ValueError):evaluate([],[])


if __name__=='__main__':unittest.main()

class CaptureFailureTests(unittest.TestCase):
    def setup_runner(self, source_ok=True, read_ok=False, inference_error=False):
        from types import SimpleNamespace
        from unittest.mock import Mock
        cap=Mock();cap.isOpened.return_value=source_ok;cap.read.return_value=(read_ok,object());cap.get.return_value=0
        cv=SimpleNamespace(VideoCapture=Mock(return_value=cap),CAP_PROP_POS_FRAMES=1,CAP_PROP_POS_MSEC=2,destroyAllWindows=Mock())
        model=Mock()
        if inference_error:model.track.side_effect=RuntimeError('inference failed')
        else:model.track.return_value=[SimpleNamespace(boxes=[])]
        ultra=SimpleNamespace(YOLO=Mock(return_value=model))
        return cap,cv,ultra
    def test_invalid_source_closes_capture(self):
        from unittest.mock import patch
        import tracker
        cap,cv,ultra=self.setup_runner(source_ok=False)
        with patch.dict(sys.modules,{'cv2':cv,'ultralytics':ultra}):
            with self.assertRaises(RuntimeError):tracker.main(['--headless','--no-cloud','--no-hardware','--source','missing.mp4'])
        cap.release.assert_called_once()
    def test_broken_looping_file_stops_after_bounded_retries(self):
        from unittest.mock import patch
        import tracker
        cap,cv,ultra=self.setup_runner()
        with patch.dict(sys.modules,{'cv2':cv,'ultralytics':ultra}):
            tracker.main(['--headless','--no-cloud','--no-hardware','--source','bad.mp4','--loop'])
        self.assertEqual(cap.read.call_count,4);cap.release.assert_called_once()
    def test_failed_camera_stops_after_five_reads(self):
        from unittest.mock import patch
        import tracker
        cap,cv,ultra=self.setup_runner()
        with patch.dict(sys.modules,{'cv2':cv,'ultralytics':ultra}),patch('tracker.time.sleep'):
            with self.assertRaises(RuntimeError):tracker.main(['--headless','--no-cloud','--no-hardware','--source','0'])
        self.assertEqual(cap.read.call_count,5);cap.release.assert_called_once()
    def test_inference_error_still_closes_hardware(self):
        from unittest.mock import Mock,patch
        import tracker
        cap,cv,ultra=self.setup_runner(read_ok=True,inference_error=True);controller=Mock()
        with patch.dict(sys.modules,{'cv2':cv,'ultralytics':ultra}),patch('tracker.ClassroomController',return_value=controller):
            with self.assertRaises(RuntimeError):tracker.main(['--headless','--no-cloud','--source','0'])
        controller.close.assert_called_once();cap.release.assert_called_once()
