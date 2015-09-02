import subprocess

import errand_boy
from errand_boy.exceptions import SessionClosedError
from errand_boy.transports import base, mock as mock_transport

from .base import mock, BaseTestCase
from .data import get_command_data


class MockTransportSimTestCase(BaseTestCase):
    def test_run_cmd(self):
        transport = mock_transport.MockTransport()

        with self.multiprocessing_patcher as multiprocessing,\
                self.subprocess_patcher as mock_subprocess:
            mock_subprocess.PIPE = subprocess.PIPE

            cmd, stdout, stderr, returncode, requests, responses = get_command_data('ls -al')

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

    def test_session(self):
        transport = mock_transport.MockTransport()

        with self.multiprocessing_patcher as multiprocessing,\
                self.subprocess_patcher as mock_subprocess:
            mock_subprocess.PIPE = subprocess.PIPE

            cmd, stdout, stderr, returncode, requests, responses = get_command_data('ls -al')

            process = mock.Mock()
            process.communicate.return_value = stdout, stderr
            process.returncode = returncode

            mock_subprocess.Popen.return_value = process

            mock_Pool = mock.Mock()
            mock_Pool.apply_async.side_effect = lambda f, args=(), kwargs={}: f(*args, **kwargs)
            multiprocessing.Pool.return_value = mock_Pool

            with transport.get_session() as session:
                foo = session.subprocess

                process = foo.Popen(cmd, shell=True, stdout=foo.PIPE, stderr=foo.PIPE)

                res_stdout, res_stderr = process.communicate()

                res_returncode = process.returncode

            with self.assertRaises(SessionClosedError):
                process.returncode

        self.assertEqual(res_stdout, stdout)
        self.assertEqual(res_stderr, stderr)
        self.assertEqual(res_returncode, returncode)

        self.assertEqual(mock_subprocess.Popen.call_count, 1)
        self.assertEqual(mock_subprocess.Popen.call_args_list[0][0][0], cmd)
