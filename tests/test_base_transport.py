import six

import errand_boy
from errand_boy.exceptions import SessionClosedError, UnknownMethodError
from errand_boy.transports import base

from .base import mock, BaseTestCase


class WorkerInitTestCase(BaseTestCase):
    def test(self):
        with mock.patch.object(base, 'setproctitle') as mock_setproctitle,\
                mock.patch.object(base.multiprocessing, 'current_process') as mock_current_process,\
                mock.patch.object(base, 'signal') as mock_signal:

            mock_current_process.return_value = mock.Mock()
            mock_current_process.return_value.name = 'foo-1'

            base.worker_init()

        self.assertEqual(mock_setproctitle.call_args_list[0][0][0], 'errand-boy worker process 1')


class RemoteObjWrapperTestCase(BaseTestCase):
    def test__send_unknown_method(self):
        session = mock.Mock()
        session.closed = False

        row = base.RemoteObjWrapper(session, 'foo')

        with self.assertRaises(UnknownMethodError):
            row._send('FOO')

    def test__send_session_closed(self):
        session = mock.Mock()
        session.closed = True

        row = base.RemoteObjWrapper(session, 'foo')

        with self.assertRaises(SessionClosedError):
            row._send('GET')


class RemoteObjRefTestCase(BaseTestCase):
    def test___init___binary(self):
        name = six.binary_type(b'foo')

        ref = base.RemoteObjRef(name)

        self.assertEqual(ref.name, name.decode('utf-8'))

    def test___init___text(self):
        name = six.text_type(u'foo')

        ref = base.RemoteObjRef(name)

        self.assertEqual(ref.name, name)

class BaseTransportTestCase(BaseTestCase):
    def setUp(self):
        super(BaseTransportTestCase, self).setUp()
        self.transport = transport = base.BaseTransport()

    def test_server_get_connection(self):
        with self.assertRaises(NotImplementedError):
            self.transport.server_get_connection()

    def test_server_recv(self):
        with self.assertRaises(NotImplementedError):
            self.transport.server_recv(None)

    def test_server_send(self):
        with self.assertRaises(NotImplementedError):
            self.transport.server_send(None, None)

    def test_server_close(self):
        self.transport.server_close(None)

    def test_server_accept(self):
        with self.assertRaises(NotImplementedError):
            self.transport.server_accept(None)

    def test_client_get_connection(self):
        with self.assertRaises(NotImplementedError):
            self.transport.client_get_connection()

    def test_client_recv(self):
        with self.assertRaises(NotImplementedError):
            self.transport.client_recv(None)

    def test_client_send(self):
        with self.assertRaises(NotImplementedError):
            self.transport.client_send(None, None)

    def test_client_close(self):
        self.transport.client_close(None)

