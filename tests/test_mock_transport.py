import mock
import unittest

import errand_boy
from errand_boy.transports import base, mock as mock_transport


class MockTransportTestCase(unittest.TestCase):
    def test(self):
        transport = mock_transport.MockTransport()
        
        with mock.patch.object(base, 'multiprocessing', autospec=True) as multiprocessing,\
                mock.patch.object(base, 'subprocess', autospec=True) as subprocess:
            
            cmd = 'ls -al'
            
            stdout, stderr = '', ''
            
            process = mock.Mock()
            process.communicate.return_value = stdout, stderr
            process.returncode = 0
            
            subprocess.Popen.return_value = process
            
            mock_Pool = mock.Mock()
            mock_Pool.apply_async.side_effect = lambda f, args=(), kwargs={}: f(*args, **kwargs)
            multiprocessing.Pool.return_value = mock_Pool
            
            result = transport.run_cmd(cmd)
        
        self.assertEqual(result[0].returncode, process.returncode)
        self.assertEqual(result[1], stdout)
        self.assertEqual(result[2], stderr)
        
        self.assertEqual(subprocess.Popen.call_count, 1)
        self.assertEqual(subprocess.Popen.call_args_list[0][0][0], cmd)
