import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
import threading
from bridge import recovering_worker
from bridge import State, Stabilizer, normalize


class BridgeTests(unittest.TestCase):
    def test_recovers_from_startup_failure(self):
        stop=threading.Event()
        state=State()
        calls=[]
        def worker(args, state, stop):
            calls.append(1)
            if len(calls)==1:
                state.update(camera='OFFLINE', model='ERROR', detail="No module named 'cv2'")
            else:
                state.update(camera='ONLINE', model='ONLINE', frame_time=time.monotonic())
                stop.set()
        with patch('bridge.camera_worker', side_effect=worker), patch.object(stop,'wait',side_effect=lambda _:stop.is_set()):
            recovering_worker(None,state,stop)
        self.assertEqual(len(calls),2)
        self.assertEqual(state.snapshot()['model'],'ONLINE')

    def test_labels_and_loss(self):
        self.assertEqual([normalize(i) for i in range(4)], ['FIST','LEFT','PALM','RIGHT'])
        stable = Stabilizer()
        self.assertEqual([stable.accept('LEFT_DIR', .9) for _ in range(3)], ['UNKNOWN','UNKNOWN','LEFT'])
        self.assertEqual(stable.accept('LEFT', .1), 'UNKNOWN')
        self.assertEqual(stable.accept('LEFT', .9), 'UNKNOWN')
        self.assertEqual(stable.accept('unrecognized', 1), 'UNKNOWN')

    def test_stalled_camera_clears_boost_but_preserves_model_status(self):
        state=State()
        state.update(gesture='PALM', confidence=1, camera='ONLINE', model='ONLINE', frame_time=time.monotonic()-1)
        result=state.snapshot()
        self.assertEqual((result['gesture'],result['camera'],result['model']),('UNKNOWN','STALE','ONLINE'))

    def test_real_udp_sender(self):
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as receiver:
            receiver.bind(('127.0.0.1',0));receiver.settimeout(5)
            process=subprocess.Popen([sys.executable,str(Path(__file__).with_name('bridge.py')),'--demo','--seconds','1','--port',str(receiver.getsockname()[1])],stdout=subprocess.PIPE)
            packets=[]
            try:
                while True:
                    packet=json.loads(receiver.recv(4096));packets.append(packet)
                    if packet['detail']=='Bridge stopped':break
                self.assertEqual(process.wait(timeout=5),0)
            finally:
                if process.poll() is None:process.kill()
                process.communicate()
            self.assertGreater(len(packets),10)
            self.assertEqual([p['seq'] for p in packets],list(range(len(packets))))
            self.assertEqual(len({p['session'] for p in packets}),1)
            self.assertEqual(packets[-1]['gesture'],'UNKNOWN')
            self.assertTrue(all(p['v']==1 for p in packets))


if __name__=='__main__':unittest.main()
