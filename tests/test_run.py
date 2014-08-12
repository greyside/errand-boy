import errand_boy
from errand_boy import run
from errand_boy.transports import unixsocket

from .base import mock, BaseTestCase


class MainTestCase(BaseTestCase):
    def test_client(self):
        argv = ['/srv/errand-boy/errand_boy/run.py', 'ls', '-al']
        cmd = ' '.join(argv[1:])
        
        with self.UNIXSocketTransport_patcher as UNIXSocketTransport,\
                self.sys_patcher as mocked_sys:
            mock_process = mock.Mock()
            mock_process.returncode = 0
            
            stdout = 'foo'
            stderr = 'bar'
            
            transport = mock.Mock()
            transport.run_cmd.return_value = stdout, stderr, mock_process.returncode
            
            UNIXSocketTransport.return_value = transport
            
            run.main(argv)
        
        self.assertEqual(transport.run_cmd.call_count, 1)
        self.assertEqual(transport.run_cmd.call_args_list[0][0][0], cmd)
        
        self.assertEqual(mocked_sys.stdout.write.call_count, 1)
        self.assertEqual(mocked_sys.stdout.write.call_args_list[0][0][0], stdout)
        
        self.assertEqual(mocked_sys.stderr.write.call_count, 1)
        self.assertEqual(mocked_sys.stderr.write.call_args_list[0][0][0], stderr)
        
        self.assertEqual(mocked_sys.exit.call_count, 1)
        self.assertEqual(mocked_sys.exit.call_args_list[0][0][0], mock_process.returncode)
    
    def test_server_no_options(self):
        argv = ['/srv/errand-boy/errand_boy/run.py']
        
        with self.UNIXSocketTransport_patcher as UNIXSocketTransport:
            transport = mock.Mock()
            
            UNIXSocketTransport.return_value = transport
            
            run.main(argv)
        
        self.assertEqual(transport.run_server.call_count, 1)
        self.assertEqual(transport.run_server.call_args_list[0][0], tuple())
        self.assertEqual(transport.run_server.call_args_list[0][1], {'max_accepts': 1000, 'pool_size': 10})
    
    def test_server_with_options(self):
        argv = ['/srv/errand-boy/errand_boy/run.py', '--max-accepts', '5']
        
        with self.UNIXSocketTransport_patcher as UNIXSocketTransport:
            transport = mock.Mock()
            
            UNIXSocketTransport.return_value = transport
            
            run.main(argv)
        
        self.assertEqual(transport.run_server.call_count, 1)
        self.assertEqual(transport.run_server.call_args_list[0][0], tuple())
        self.assertEqual(transport.run_server.call_args_list[0][1], {'max_accepts': int(argv[2]), 'pool_size': 10})

