import collections
import logging
import multiprocessing
import numbers
import pickle
import signal
import subprocess
import six
import sys
import uuid

from .. import constants
from .. import __version__
from ..exceptions import DisconnectedError, SessionClosedError, UnknownMethodError


logger = logging.getLogger(__name__)

RAW_TYPES = six.string_types+(six.binary_type, numbers.Number, BaseException)

try:
    from setproctitle import setproctitle
except ImportError:
    logger.info('Cannot set process name.')
    setproctitle = lambda title: None


class ClientSession(object):
    def __init__(self, transport):
        self.transport = transport
        self.connection = transport.client_get_connection()
        self._closed = True

    @property
    def closed(self):
        return self._closed

    def __getattr__(self, name):
        return RemoteObjWrapper(self, name)

    def __enter__(self):
        self._closed = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._closed = True
        try:
            self.transport.client_close(self.connection)
        except Exception as e:
            logger.exception(e)

        # we don't want to hide AttributeErrors, etc. from end user
        return False


class RemoteObjRef(object):
    def __init__(self, name):
        if hasattr(name, 'decode'):
            name = name.decode('utf-8')
        self.name = name

    def __str__(self):
        return self.name


class RemoteObjWrapper(object):
    _patch_functions = ['next', '__next__', '__iter__']

    def __init__(self, session, name):
        self.session = session
        self.name = name

        self._property_cache = {}

        for name in self._patch_functions:
            self._property_cache[name] = None

    def _send(self, method, *args, **kwargs):
        session = self.session

        if session.closed:
            raise SessionClosedError()

        if method == 'GET':
            func = session.transport.send_get_request
        elif method == 'CALL':
            func = session.transport.send_call_request
        else:
            raise UnknownMethodError(method)

        ret = func(session.connection, self.name, *args, **kwargs)

        if isinstance(ret, RemoteObjRef):
            ret = RemoteObjWrapper(session, ret.name)

        return ret

    def __getattr__(self, name):
        return self._send('GET', name)

    def __call__(self, *args, **kwargs):
        return self._send('CALL', *args, **kwargs)

    def _get_prop(self, name):
        val = self._property_cache[name]
        if val:
            return val
        self._property_cache[name] = self.__getattr__(name)
        return self._property_cache[name]

    @property
    def next(self):
        return self._get_prop('next')

    @property
    def __next__(self):
        return self._get_prop('__next__')

    @property
    def __iter__(self):
        return self._get_prop('__iter__')


class Request(object):
    def __init__(self, method, path, headers, body):
        self.method = method
        self.path = path
        self.headers = headers
        self.body = body


class Response(object):
    def __init__(self, status, headers, body):
        self.status = status
        self.headers = headers
        self.body = body


def worker_init(*args):
    name = multiprocessing.current_process().name
    logger.debug('Worker initialized: {}'.format(name))
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    setproctitle('errand-boy worker process {}'.format(name.split('-')[1]))


def worker(self, connection):
    logger.debug('worker connected')
    self.server_handle_client(connection)


class BaseTransport(object):
    """
    Base class providing functionality common to all transports.
    """

    def __init__(self):
        pass

    def connection_to_string(self, connection):
        return repr(connection)

    def server_get_connection(self):
        raise NotImplementedError()

    def server_recv(self, connection):
        raise NotImplementedError()

    def server_send(self, connection, data):
        raise NotImplementedError()

    def server_close(self, connection):
        pass

    def translate_obj(self, exposed_locals, val):
        if isinstance(val, RemoteObjRef):
            val = exposed_locals[val.name]
        return val

    def server_serialize(self, exposed_locals, obj):
        if obj is not None and not isinstance(obj, RAW_TYPES):
            name = six.text_type(uuid.uuid4())
            exposed_locals[name] = obj
            obj = RemoteObjRef(name)
        return obj

    def server_handle_client(self, connection):
        connection = self.server_deserialize_connection(connection)

        logger.debug('server_handle_client: {}'.format(self.connection_to_string(connection)))

        exposed_locals = {'subprocess': subprocess}

        while True:
            # need to close connection when client not listening
            try:
                 request = self.get_request(connection)
            except DisconnectedError:
                 break

            raised = False
            obj = None

            if request.method == 'GET':
                name, attr = request.path.split('.')
                try:
                    obj = getattr(exposed_locals[name], attr)
                except KeyError as e:
                    obj = e
                    raised = True
            elif request.method == 'CALL':
                name = request.path
                try:
                    obj = exposed_locals[name]
                except KeyError as e:
                    obj = e
                    raised = True

                args, kwargs = pickle.loads(request.body)

                args = [self.translate_obj(exposed_locals, arg) for arg in args]

                for key in kwargs:
                    kwargs[key] = self.translate_obj(exposed_locals, kwargs[key])

                try:
                    obj = obj(*args, **kwargs)
                except Exception as e:
                    obj = e
                    raised = True

            obj = self.server_serialize(exposed_locals, obj)

            self.send_response(connection, obj, raised=raised)

        self.server_close(connection)

    def server_accept(self, serverconnection):
        raise NotImplementedError()

    def server_deserialize_connection(self, connection):
        return connection

    def server_serialize_connection(self, connection):
        return connection

    def run_server(self, pool_size=10, max_accepts=5000, max_child_tasks=100):
        setproctitle('errand-boy master process')

        serverconnection = self.server_get_connection()

        logger.info('Accepting connections: {}'.format(self.connection_to_string(serverconnection)))
        logger.info('pool_size: {}'.format(pool_size))
        logger.info('max_accepts: {}'.format(max_accepts))
        logger.info('max_child_tasks: {}'.format(max_child_tasks))

        pool = multiprocessing.Pool(pool_size, worker_init, tuple(), max_child_tasks)

        connections = []

        remaining_accepts = max_accepts

        if not remaining_accepts:
            remaining_accepts = True

        try:
            while remaining_accepts:
                connection = self.server_accept(serverconnection)

                logger.info('Accepted connection from: {}'.format(self.connection_to_string(connection)))

                result = pool.apply_async(worker, [self, self.server_serialize_connection(connection)])

                connection = None

                if remaining_accepts is not True:
                    remaining_accepts -= 1
        except KeyboardInterrupt:
            logger.info('Received KeyboardInterrupt')
            pool.terminate()
        except Exception as e:
            logger.exception(e)
            pool.terminate()
            raise
        finally:
            pool.close()
            pool.join()

    def client_get_connection(self):
        raise NotImplementedError()

    def client_recv(self, connection):
        raise NotImplementedError()

    def client_send(self, connection, command_string):
        raise NotImplementedError()

    def client_close(self, connection):
        pass

    def send_algo(self, connection, send_func, first_line, headers=None, body=None):
        CRLF = constants.CRLF
        msg = [first_line]
        msg.append(CRLF)

        if headers:
            for name, val in headers:
                msg.append('{}: {}'.format(name, val))
                msg.append(CRLF)

        msg.append('Content-Length: {}'.format(len(body)))
        msg.append(CRLF)

        if body:
            msg.append(CRLF)
            msg.append(body)

        msg = [s.encode('utf-8') if hasattr(s, 'encode') else s for s in msg]

        msg = b''.join(msg)

        return send_func(connection, msg)

    def send_request(self, connection, method, path, body=''):
        first_line = "{method} {path}".format(method=method, path=path)
        self.send_algo(connection, self.client_send, first_line, headers=None, body=body)

        resp = self.get_response(connection)

        obj = pickle.loads(resp.body)

        if resp.status == 400:
            raise obj

        return obj

    def send_get_request(self, connection, prefix, name):
        return self.send_request(connection, 'GET', prefix+'.'+name)

    def send_call_request(self, connection, name, *args, **kwargs):
        kwargs = collections.OrderedDict(sorted(kwargs.items(), key=lambda t: t[0]))
        body = pickle.dumps([args, kwargs])

        return self.send_request(connection, 'CALL', name, body=body)

    def recv_algo(self, connection, recv_func):
        CRLF = constants.CRLF

        lines = []
        data = b''

        content_length = None

        while True:
            new_data = recv_func(connection, 4096)

            if not new_data:
                raise DisconnectedError()

            data += new_data

            if not lines and CRLF in data:
                try:
                    headers, body = data.split(CRLF + CRLF, 1)
                except ValueError:
                    split_data = data.split(CRLF)
                    lines.extend(split_data[:-1])
                    data = split_data[-1]
                else:
                    lines.extend((headers + CRLF).split(CRLF))
                    data = body

            if lines and content_length is None:
                for line in lines:
                    try:
                        header, val = line.split(b': ')
                        if header.lower() == b'content-length':
                            content_length = int(val)
                            break
                    except ValueError:
                        pass

            if content_length == 0 and len(lines) > 1:
                break

            if len(lines) > 2 and lines[-1] == b'':
                # needs length of body, minus already fetched data
                remaining_len = content_length - len(data)

                if remaining_len:
                    data += recv_func(connection, remaining_len)

                # only break once all data has been returned
                if len(data) == content_length:
                    break

        if data:
            data = CRLF + data
        data = CRLF.join(lines) + data

        try:
            headers, body = data.split(CRLF+CRLF)
        except ValueError:
            headers = data
            body = b''

        headers = headers.split(CRLF)
        headers = [header.decode('utf-8') for header in headers]
        first_line = headers[0]
        headers = headers[1:]

        headers = [header.split(': ') for header in headers]
        return first_line, headers, body

    def get_request(self, connection):
        first_line, headers, body = self.recv_algo(connection, self.server_recv)

        method, path = first_line.split(' ', 1)

        return Request(method, path, headers, body)

    def send_response(self, connection, obj, raised=False):
        body = pickle.dumps(obj)

        first_line = '200 OK' if not raised else '400 Error'

        return self.send_algo(connection, self.server_send, first_line, body=body)

    def get_response(self, connection):
        first_line, headers, body = self.recv_algo(connection, self.client_recv)

        status = int(first_line.split()[0])

        return Response(status, headers, body)

    def get_session(self):
        return ClientSession(self)

    def run_cmd(self, command_string):
        with self.get_session() as session:
            subprocess = session.subprocess

            process = subprocess.Popen(command_string, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stdout, stderr = process.communicate()

            returncode = process.returncode

        return stdout, stderr, returncode
