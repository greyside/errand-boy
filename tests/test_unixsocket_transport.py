import six
import subprocess

import errand_boy
from errand_boy.exceptions import SessionClosedError
from errand_boy.transports import base, unixsocket

from .base import mock, BaseTestCase
from .data import get_command_data


class UNIXSocketTransportTestCase(BaseTestCase):
    def setUp(self):
        super(UNIXSocketTransportTestCase, self).setUp()
        self.transport = unixsocket.UNIXSocketTransport()

    def test_server_close(self):
        connection = mock.Mock(), ''

        self.transport.server_close(connection)

        self.assertEqual(connection[0].close.call_count, 1)

    def test_server_close_error(self):
        connection = mock.Mock(), ''
        connection[0].close.side_effect = Exception('Catch me if you can.')

        self.transport.server_close(connection)

        self.assertEqual(connection[0].close.call_count, 1)

    def test_client_close(self):
        connection = mock.Mock()

        self.transport.client_close(connection)

        self.assertEqual(connection.close.call_count, 1)

    def test_client_close_error(self):
        connection = mock.Mock()
        connection.close.side_effect = Exception('Catch me if you can.')

        self.transport.client_close(connection)

        self.assertEqual(connection.close.call_count, 1)


class UNIXSocketTransportClientSimTestCase(BaseTestCase):
    def test_run_cmd(self):
        transport = unixsocket.UNIXSocketTransport()

        with self.socket_patcher as socket:
            clientsocket = mock.Mock()

            cmd, stdout, stderr, returncode, requests, responses = get_command_data('ls -al')

            clientsocket.recv.side_effect = iter(responses)

            socket.socket.return_value = clientsocket

            result = transport.run_cmd(cmd)

        self.assertEqual(clientsocket.connect.call_count, 1)
        self.assertEqual(clientsocket.connect.call_args_list[0][0][0], '/tmp/errand-boy')

        self.assertEqual(clientsocket.sendall.call_count, len(requests)-1)

        for i, request in enumerate(requests[:-1]):
            self.assertEqual(clientsocket.sendall.call_args_list[i][0][0], request)

        self.assertEqual(clientsocket.recv.call_count, len(responses))

        self.assertEqual(result[0], stdout)
        self.assertEqual(result[1], stderr)
        self.assertEqual(result[2], returncode)

    def test_session(self):
        transport = unixsocket.UNIXSocketTransport()

        with self.socket_patcher as socket:
            clientsocket = mock.Mock()

            cmd, stdout, stderr, returncode, requests, responses = get_command_data('ls -al')

            clientsocket.recv.side_effect = iter(responses)

            socket.socket.return_value = clientsocket

            with transport.get_session() as session:
                foo = session.subprocess

                process = foo.Popen(cmd, shell=True, stdout=foo.PIPE, stderr=foo.PIPE)

                res_stdout, res_stderr = process.communicate()

                res_returncode = process.returncode

            with self.assertRaises(SessionClosedError) as e:
                process.returncode

        self.assertEqual(clientsocket.connect.call_count, 1)
        self.assertEqual(clientsocket.connect.call_args_list[0][0][0], '/tmp/errand-boy')

        self.assertEqual(clientsocket.sendall.call_count, len(requests)-1)

        for i, request in enumerate(requests[:-1]):
            self.assertEqual(clientsocket.sendall.call_args_list[i][0][0], request)

        self.assertEqual(clientsocket.recv.call_count, len(responses))

        self.assertEqual(res_stdout, stdout)
        self.assertEqual(res_stderr, stderr)
        self.assertEqual(res_returncode, returncode)


class UNIXSocketTransportServerSimTestCase(BaseTestCase):
    def test(self):
        transport = unixsocket.UNIXSocketTransport()

        with self.socket_patcher as socket,\
                self.reduce_socket_patcher as reduce_socket,\
                self.rebuild_socket_patcher as rebuild_socket,\
                self.multiprocessing_patcher as multiprocessing,\
                self.subprocess_patcher as mock_subprocess,\
                self.uuid_patcher as uuid:
            mock_subprocess.PIPE = subprocess.PIPE

            serversocket = mock.Mock()

            cmd, stdout, stderr, returncode, requests, responses = get_command_data('ls -al')

            process = mock.Mock()
            process.communicate.return_value = stdout, stderr
            process.returncode = returncode

            mock_subprocess.Popen.return_value = process

            uuid.side_effect = ('obj%s' % i for i in six.moves.range(1, 20))

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

        self.assertEqual(clientsocket.recv.call_count, len(requests))

        self.assertEqual(mock_subprocess.Popen.call_count, 1)
        self.assertEqual(mock_subprocess.Popen.call_args_list[0][0][0], cmd)

        self.assertEqual(clientsocket.sendall.call_count, len(responses))
        for i, response in enumerate(responses):
            self.assertEqual(clientsocket.sendall.call_args_list[i][0][0], response)

    def test_max_accepts_zero(self):
        transport = unixsocket.UNIXSocketTransport()

        with self.socket_patcher as socket,\
                self.reduce_socket_patcher as reduce_socket,\
                self.rebuild_socket_patcher as rebuild_socket,\
                self.multiprocessing_patcher as multiprocessing,\
                self.subprocess_patcher as mock_subprocess,\
                self.uuid_patcher as uuid:
            mock_subprocess.PIPE = subprocess.PIPE

            serversocket = mock.Mock()

            cmd, stdout, stderr, returncode, requests, responses = get_command_data('ls -al')

            process = mock.Mock()
            process.communicate.return_value = stdout, stderr
            process.returncode = returncode

            mock_subprocess.Popen.return_value = process

            uuid.side_effect = ('obj%s' % i for i in six.moves.range(1, 20))

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

        self.assertEqual(clientsocket.recv.call_count, len(requests))

        self.assertEqual(mock_subprocess.Popen.call_count, 1)
        self.assertEqual(mock_subprocess.Popen.call_args_list[0][0][0], cmd)

        self.assertEqual(clientsocket.sendall.call_count, len(responses))
        for i, response in enumerate(responses):
            self.assertEqual(clientsocket.sendall.call_args_list[i][0][0], response)
