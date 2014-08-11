try:
    from unittest import mock
except ImportError:
    import mock
import unittest

from errand_boy import run
from errand_boy.transports import base, mock as mock_transport, unixsocket


class BaseTestCase(unittest.TestCase):
    subprocess_patcher = mock.patch.object(base, 'subprocess', autospec=True)
    multiprocessing_patcher = mock.patch.object(base, 'multiprocessing', autospec=True)
    sys_patcher = mock.patch.object(run, 'sys', autospec=True)
    uuid_patcher = mock.patch.object(base.uuid, 'uuid4', autospec=True)
    
    UNIXSocketTransport_patcher = mock.patch.object(unixsocket, 'UNIXSocketTransport', autospec=True)
    socket_patcher = mock.patch.object(unixsocket, 'socket', autospec=True)
    reduce_socket_patcher = mock.patch.object(unixsocket, 'reduce_socket', autospec=True)
    rebuild_socket_patcher = mock.patch.object(unixsocket, 'rebuild_socket', autospec=True)
