import pickle
import six

import errand_boy
from errand_boy.transports import base, unixsocket

from .base import mock, BaseTestCase
from .data import commands, get_command_data, get_req, get_resp


class UNIXSocketTransportClientTestCase(BaseTestCase):
    def test_run_cmd(self):
        transport = unixsocket.UNIXSocketTransport()
        
        with self.socket_patcher as socket:
            clientsocket = mock.Mock()
            
            cmd = 'ls -al'
            
            stdout, stderr, returncode = get_command_data(cmd)
            
            requests = [
                get_req('GET', 'subprocess.Popen'),
                get_req('CALL', 'obj1', [(cmd,), {}]),
                get_req('GET', 'obj2.communicate'),
                get_req('CALL', 'obj3', [tuple(), {}]),
                get_req('GET', 'obj4.__iter__'),
                get_req('CALL', 'obj5', [tuple(), {}]),
                get_req('GET', 'obj6.next' if six.PY2 else 'obj6.__next__'),
                get_req('CALL', 'obj7', [tuple(), {}]),
                get_req('CALL', 'obj7', [tuple(), {}]),
                get_req('CALL', 'obj7', [tuple(), {}]),
                get_req('GET', 'obj2.returncode'),
            ]
            
            responses = [
                get_resp('200 OK', base.Proxy('obj1')),
                get_resp('200 OK', base.Proxy('obj2')),
                get_resp('200 OK', base.Proxy('obj3')),
                get_resp('200 OK', base.Proxy('obj4')),
                get_resp('200 OK', base.Proxy('obj5')),
                get_resp('200 OK', base.Proxy('obj6')),
                get_resp('200 OK', base.Proxy('obj7')),
                get_resp('200 OK', stdout),
                get_resp('200 OK', stderr),
                get_resp('400 Error', StopIteration()),
                get_resp('200 OK', returncode),
            ]
            
            clientsocket.recv.side_effect = iter(responses)
            
            socket.socket.return_value = clientsocket
            
            result = transport.run_cmd(cmd)
        
        self.assertEqual(clientsocket.connect.call_count, 1)
        self.assertEqual(clientsocket.connect.call_args_list[0][0][0], '/tmp/errand-boy')
        
        self.assertEqual(clientsocket.sendall.call_count, len(responses))
        for i, request in enumerate(requests):
            self.assertEqual(clientsocket.sendall.call_args_list[i][0][0], request)
        
        self.assertEqual(clientsocket.recv.call_count, len(requests))
        
        self.assertEqual(result[1], stdout)
        self.assertEqual(result[2], stderr)
        self.assertEqual(result[3], returncode)


class UNIXSocketTransportServerTestCase(BaseTestCase):
    def test(self):
        transport = unixsocket.UNIXSocketTransport()
        
        with self.socket_patcher as socket,\
                self.reduce_socket_patcher as reduce_socket,\
                self.rebuild_socket_patcher as rebuild_socket,\
                self.multiprocessing_patcher as multiprocessing,\
                self.subprocess_patcher as subprocess,\
                self.uuid_patcher as uuid:
            
            serversocket = mock.Mock()
            
            
            cmd = 'ls -al'
            
            stdout, stderr, returncode = get_command_data(cmd)
            
            process = mock.Mock()
            process.communicate.return_value = stdout, stderr
            process.returncode = returncode
            
            subprocess.Popen.return_value = process
            
            uuid.side_effect = ('obj%s' % i for i in six.moves.range(1, 20))
            
            requests = [
                get_req('GET', 'subprocess.Popen'),
                get_req('CALL', 'obj1', [(cmd,), {}]),
                get_req('GET', 'obj2.communicate'),
                get_req('CALL', 'obj3', [tuple(), {}]),
                get_req('GET', 'obj4.__iter__'),
                get_req('CALL', 'obj5', [tuple(), {}]),
                get_req('GET', 'obj6.next' if six.PY2 else 'obj6.__next__'),
                get_req('CALL', 'obj7', [tuple(), {}]),
                get_req('CALL', 'obj7', [tuple(), {}]),
                get_req('CALL', 'obj7', [tuple(), {}]),
                get_req('GET', 'obj2.returncode'),
            ]
            
            responses = [
                get_resp('200 OK', base.Proxy('obj1')),
                get_resp('200 OK', base.Proxy('obj2')),
                get_resp('200 OK', base.Proxy('obj3')),
                get_resp('200 OK', base.Proxy('obj4')),
                get_resp('200 OK', base.Proxy('obj5')),
                get_resp('200 OK', base.Proxy('obj6')),
                get_resp('200 OK', base.Proxy('obj7')),
                get_resp('200 OK', stdout),
                get_resp('200 OK', stderr),
                get_resp('400 Error', StopIteration()),
                get_resp('200 OK', returncode),
            ]
            
            clientsocket = mock.Mock()
            clientsocket.recv.side_effect = iter(requests)
            
            serversocket.accept.return_value = clientsocket, ''
            
            socket.socket.return_value = serversocket
            
            reduce_socket.return_value = (reduce_socket, ('I\'m a socket, NOT!', '', '', '',))
            rebuild_socket.return_value = clientsocket
            
            
            mock_Pool = mock.Mock()
            mock_Pool.apply_async.side_effect = lambda f, args=(), kwargs={}: f(*args, **kwargs)
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
        
        self.assertEqual(clientsocket.recv.call_count, len(requests)+1)
        
        self.assertEqual(subprocess.Popen.call_count, 1)
        self.assertEqual(subprocess.Popen.call_args_list[0][0][0], cmd)
        
        self.assertEqual(clientsocket.sendall.call_count, len(responses))
        for i, response in enumerate(responses):
            self.assertEqual(clientsocket.sendall.call_args_list[i][0][0], response)
    
    def test_max_accepts_zero(self):
        transport = unixsocket.UNIXSocketTransport()
        
        with self.socket_patcher as socket,\
                self.reduce_socket_patcher as reduce_socket,\
                self.rebuild_socket_patcher as rebuild_socket,\
                self.multiprocessing_patcher as multiprocessing,\
                self.subprocess_patcher as subprocess,\
                self.uuid_patcher as uuid:
            
            serversocket = mock.Mock()
            
            
            cmd = 'ls -al'
            
            stdout, stderr, returncode = get_command_data(cmd)
            
            process = mock.Mock()
            process.communicate.return_value = stdout, stderr
            process.returncode = returncode
            
            subprocess.Popen.return_value = process
            
            uuid.side_effect = ('obj%s' % i for i in six.moves.range(1, 20))
            
            requests = [
                get_req('GET', 'subprocess.Popen'),
                get_req('CALL', 'obj1', [(cmd,), {}]),
                get_req('GET', 'obj2.communicate'),
                get_req('CALL', 'obj3', [tuple(), {}]),
                get_req('GET', 'obj2.returncode'),
            ]
            
            responses = [
                get_resp('200 OK', base.Proxy('obj1')),
                get_resp('200 OK', base.Proxy('obj2')),
                get_resp('200 OK', base.Proxy('obj3')),
                get_resp('200 OK', base.Proxy('obj4')),
                get_resp('200 OK', returncode),
            ]
            
            clientsocket = mock.Mock()
            clientsocket.recv.side_effect = iter(requests)
            
            serversocket.accept.side_effect = iter([(clientsocket, '',)])
            
            socket.socket.return_value = serversocket
            
            reduce_socket.return_value = (reduce_socket, ('I\'m a socket, NOT!', '', '', '',))
            rebuild_socket.return_value = clientsocket
            
            
            mock_Pool = mock.Mock()
            mock_Pool.apply_async.side_effect = lambda f, args=(), kwargs={}: f(*args, **kwargs)
            multiprocessing.Pool.return_value = mock_Pool
            
            # serve until an error happens (in ths case StopIteration from running
            # out of items in clientsocket.recv.side_effect)
            try:
                transport.run_server(max_accepts=0)
            except StopIteration:
                pass
        
        self.assertEqual(serversocket.bind.call_count, 1)
        self.assertEqual(serversocket.bind.call_args_list[0][0][0], '/tmp/errand-boy')
        
        self.assertEqual(serversocket.listen.call_count, 1)
        self.assertEqual(serversocket.listen.call_args_list[0][0][0], 5)
        
        self.assertEqual(reduce_socket.call_count, 1)
        self.assertEqual(reduce_socket.call_args_list[0][0][0], clientsocket)
        
        self.assertEqual(rebuild_socket.call_count, 1)
        self.assertEqual(rebuild_socket.call_args_list[0][0], reduce_socket.return_value[1])
        
        self.assertEqual(clientsocket.recv.call_count, len(requests)+1)
        
        self.assertEqual(subprocess.Popen.call_count, 1)
        self.assertEqual(subprocess.Popen.call_args_list[0][0][0], cmd)
        
        self.assertEqual(clientsocket.sendall.call_count, len(responses))
        for i, response in enumerate(responses):
            self.assertEqual(clientsocket.sendall.call_args_list[i][0][0], response)
