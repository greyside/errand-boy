import subprocess

import errand_boy
from errand_boy.transports import base, mock as mock_transport

from .base import mock, BaseTestCase
from .data import get_command_data

class MockTransportTestCase(BaseTestCase):
    def test(self):
        transport = mock_transport.MockTransport()
        
        with self.multiprocessing_patcher as multiprocessing,\
                self.subprocess_patcher as mock_subprocess:
            mock_subprocess.PIPE = subprocess.PIPE
            
            cmd = 'ls -al'
            
            stdout, stderr, returncode = get_command_data(cmd)
            
            process = mock.Mock()
            process.communicate.return_value = stdout, stderr
            process.returncode = returncode
            
            mock_subprocess.Popen.return_value = process
            
            mock_Pool = mock.Mock()
            mock_Pool.apply_async.side_effect = lambda f, args=(), kwargs={}: f(*args, **kwargs)
            multiprocessing.Pool.return_value = mock_Pool
            
            result = transport.run_cmd(cmd)
        
        self.assertEqual(result[0], stdout)
        self.assertEqual(result[1], stderr)
        self.assertEqual(result[2], returncode)
        
        self.assertEqual(mock_subprocess.Popen.call_count, 1)
        self.assertEqual(mock_subprocess.Popen.call_args_list[0][0][0], cmd)
