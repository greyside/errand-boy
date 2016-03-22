import six
import subprocess
import sys
import time
import unittest

import errand_boy
from errand_boy.constants import CRLF
from errand_boy.exceptions import SessionClosedError
from errand_boy.transports import base, unixsocket

from .base import BaseTestCase


class UNIXSocketTransportLiveTestCase(unittest.TestCase):
    def setUp(self):
        print(sys.executable)
        self.server_process = subprocess.Popen(
            sys.executable + ' -m errand_boy.run',
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        # we need to wait for the server to create the socket before we can
        # connect.
        time.sleep(1)

    def tearDown(self):
        self.server_process.terminate()

    def test_large_amount_of_data(self):
        """
        https://github.com/greyside/errand-boy/issues/1
        """

        transport = unixsocket.UNIXSocketTransport()

        str_data = (b'a' * 244544) + b'b'

        with transport.get_session() as session:
            foo = session.subprocess

            process = foo.Popen(['cat'], stdin=foo.PIPE,
                stdout=foo.PIPE,
                stderr=foo.PIPE
            )

            res_stdout, res_stderr = process.communicate(str_data)

            res_returncode = process.returncode

        self.assertEqual(res_stdout, str_data)

    def test_crlf_in_body(self):
        transport = unixsocket.UNIXSocketTransport()

        str_data = b'foo' + CRLF + b'bar'

        with transport.get_session() as session:
            foo = session.subprocess

            process = foo.Popen(['cat'], stdin=foo.PIPE,
                stdout=foo.PIPE,
                stderr=foo.PIPE
            )

            res_stdout, res_stderr = process.communicate(str_data)

            res_returncode = process.returncode

        self.assertEqual(res_stdout, str_data)
