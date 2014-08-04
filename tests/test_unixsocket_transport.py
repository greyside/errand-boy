import mock
import unittest

import errand_boy
from errand_boy.transports import base, unixsocket

class UNIXSocketTransportClientTestCase(unittest.TestCase):
    def test(self):
        transport = unixsocket.UNIXSocketTransport()
        
        with mock.patch.object(unixsocket, 'socket', autospec=True) as socket:
            clientsocket = mock.Mock()
            
            cmd = 'ls -al'
            
            expected_result = base.ProcessResult(
                VERSION=errand_boy.__version__,
                command_string=cmd,
                returncode=0,
                stdout='',
                stderr='',
            )
            
            recv_data = "0:1:\r\n\r\n0"
            
            clientsocket.recv.side_effect = iter([recv_data[:1], recv_data[1:], '',])
            
            socket.socket.return_value = clientsocket
            
            result = transport.run_cmd(cmd)
        
        self.assertEqual(clientsocket.connect.call_count, 1)
        self.assertEqual(clientsocket.connect.call_args_list[0][0][0], '/tmp/errand-boy')
        
        self.assertEqual(clientsocket.sendall.call_count, 2)
        self.assertEqual(clientsocket.sendall.call_args_list[0][0][0], cmd+'\r\n\r\n')
        self.assertEqual(clientsocket.sendall.call_args_list[1][0][0], '\r\n\r\n')
        
        self.assertEqual(clientsocket.recv.call_count, 3)
        
        self.assertEqual(result, expected_result)

class UNIXSocketTransportServerTestCase(unittest.TestCase):
    def test(self):
        transport = unixsocket.UNIXSocketTransport()
        
        with mock.patch.object(unixsocket, 'socket', autospec=True) as socket,\
                mock.patch.object(unixsocket.reduction, 'reduce_socket', autospec=True) as reduce_socket,\
                mock.patch.object(unixsocket.reduction, 'rebuild_socket', autospec=True) as rebuild_socket,\
                mock.patch.object(base, 'multiprocessing', autospec=True) as multiprocessing,\
                mock.patch.object(base, 'subprocess', autospec=True) as subprocess:
            
            serversocket = mock.Mock()
            
            cmd = 'ls -al'
            
            stdout, stderr= '', ''
            
            process = mock.Mock()
            process.communicate.return_value = stdout, stderr
            process.returncode = 0
            
            subprocess.Popen.return_value = process
            
            clientsocket = mock.Mock()
            clientsocket.recv.side_effect = iter([cmd[:2], cmd[2:], '\r', '\n\r', '\nfoo', 'bar', '\r\n\r\n', '',])
            
            serversocket.accept.return_value = clientsocket, ''
            
            socket.socket.return_value = serversocket
            
            reduce_socket.return_value = (reduce_socket, ('I\'m a socket, NOT!', '', '', '',))
            rebuild_socket.return_value = clientsocket
            
            
            mock_Pool = mock.Mock()
            def apply_async(func, args=(), kwargs={}):
                return func(*args, **kwargs)
            mock_Pool.apply_async.side_effect = apply_async
            multiprocessing.Pool.return_value = mock_Pool
            
            transport.run_server(max_accepts=1)
        
        self.assertEqual(serversocket.bind.call_count, 1)
        self.assertEqual(serversocket.bind.call_args_list[0][0][0], '/tmp/errand-boy')
        
        self.assertEqual(serversocket.listen.call_count, 1)
        self.assertEqual(serversocket.listen.call_args_list[0][0][0], 5)
        
        self.assertEqual(reduce_socket.call_count, 1)
        self.assertEqual(reduce_socket.call_args_list[0][0][0], clientsocket)
        
        self.assertEqual(rebuild_socket.call_count, 1)
        self.assertEqual(rebuild_socket.call_args_list[0][0], reduce_socket.return_value[1])
        
        self.assertEqual(clientsocket.recv.call_count, 8)
        
        self.assertEqual(subprocess.Popen.call_count, 1)
        self.assertEqual(subprocess.Popen.call_args_list[0][0][0], cmd)
        
        self.assertEqual(clientsocket.sendall.call_count, 1)
        self.assertEqual(clientsocket.sendall.call_args_list[0][0][0], '\r\n\r\n0')
        
        self.assertEqual(clientsocket.close.call_count, 1)

