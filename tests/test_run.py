import mock
import unittest

import errand_boy
from errand_boy.run import main
from errand_boy.transports import base, unixsocket

class MainTestCase(unittest.TestCase):
    def test_client(self):
        argv = ['/srv/errand-boy/errand_boy/run.py', 'ls', '-al']
        cmd = ' '.join(argv[1:])
        
        with mock.patch.object(unixsocket, 'UNIXSocketTransport', autospec=True) as UNIXSocketTransport:
            transport = mock.Mock()
            
            UNIXSocketTransport.return_value = transport
            
            main(argv)
        
        self.assertEqual(transport.run_cmd.call_count, 1)
        self.assertEqual(transport.run_cmd.call_args_list[0][0][0], cmd)
    
    def test_server(self):
        argv = ['/srv/errand-boy/errand_boy/run.py', 'server']
        
        with mock.patch.object(unixsocket, 'UNIXSocketTransport', autospec=True) as UNIXSocketTransport:
            transport = mock.Mock()
            
            UNIXSocketTransport.return_value = transport
            
            main(argv)
        
        self.assertEqual(transport.run_server.call_count, 1)

