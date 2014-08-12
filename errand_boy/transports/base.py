import logging
import multiprocessing
import numbers
import pickle
import signal
import subprocess
import sys
import uuid

from .. import constants
from .. import __version__


logger = logging.getLogger(__name__)

try:
    from setproctitle import setproctitle
except ImportError:
    logger.info('Cannot set process name.')
    setproctitle = lambda title: None


class Proxy(object):
    def __init__(self, name):
        self.name = name
    
    def __str__(self):
        return str(self.name)


class ClientProxy(object):
    def __init__(self, transport, connection, proxy):
        self.transport = transport
        self.connection = connection
        self.proxy = proxy
        self._next = None
        self.___iter__ = None
    
    def __getattr__(self, name):
        ret = self.transport.send_get_request(self.connection, self.proxy, name)
        if isinstance(ret, Proxy):
            ret = ClientProxy(self.transport, self.connection, ret)
        return ret
    
    @property
    def next(self):
        if self._next:
            return self._next
        self._next = self.__getattr__('next')
        return self._next
    
    @property
    def __iter__(self):
        if self.___iter__:
            return self.___iter__
        self.___iter__ = self.__getattr__('__iter__')
        return self.___iter__
    
    def __call__(self, *args, **kwargs):
        ret = self.transport.send_call_request(self.connection, self.proxy, *args, **kwargs)
        if isinstance(ret, Proxy):
            ret = ClientProxy(self.transport, self.connection, ret)
        return ret


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
        pass
    
    def server_recv(self, connection):
        pass
    
    def server_send(self, connection, data):
        pass
    
    def server_close(self, connection):
        pass
    
    def translate_obj(self, exposed_locals, val):
        if isinstance(val, Proxy):
            val = exposed_locals[val.name]
        return val
    
    def server_serialize(self, exposed_locals, obj):
        if not isinstance(obj, (basestring, numbers.Number, BaseException)):
            name = str(uuid.uuid4())
            exposed_locals[name] = obj
            obj = Proxy(name)
        return obj
    
    def server_handle_client(self, connection):
        connection = self.server_deserialize_connection(connection)
        
        logger.debug('server_handle_client: {}'.format(self.connection_to_string(connection)))
        
        exposed_locals = {'subprocess': subprocess}
        
        while True:
            try:
                 request = self.get_request(connection)
            except:
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
                obj = exposed_locals[name]
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
        
        return
    
    def server_accept(self, serverconnection):
        pass
    
    def server_deserialize_connection(self, connection):
        return connection
    
    def server_serialize_connection(self, connection):
        return connection
    
    def run_server(self, pool_size=10, max_accepts=1000):
        setproctitle('errand-boy master process')
        
        serverconnection = self.server_get_connection()
        
        logger.info('Accepting connections: {}'.format(self.connection_to_string(serverconnection)))
        logger.info('pool_size: {}'.format(pool_size))
        logger.info('max_accepts: {}'.format(max_accepts))
        
        pool = multiprocessing.Pool(pool_size, worker_init)
        
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
        pass
    
    def client_send(self, connection, command_string):
        pass
    
    def client_recv(self, connection):
        pass
    
    def client_close(self, connection):
        pass
    
    def send_request(self, connection, method, path, data=''):
        CRLF = constants.CRLF
        msg = ["{method} {path}".format(method=method, path=path)]
        msg.append(CRLF)
        
        msg.append('Content-Length: {}'.format(len(data)))
        msg.append(CRLF)
        
        if data:
            msg.append(CRLF)
            msg.append(data)
        
        msg = ''.join(msg)
        
        self.client_send(connection, msg)
        
        resp = self.get_response(connection)
        
        obj = pickle.loads(resp.body)
        
        if resp.status == 400:
            raise obj
        
        return obj
    
    def send_get_request(self, connection, clientproxy, name):
        return self.send_request(connection, 'GET', clientproxy.name+'.'+name)
    
    def send_call_request(self, connection, clientproxy, *args, **kwargs):
        data = pickle.dumps([args, kwargs])
        
        return self.send_request(connection, 'CALL', clientproxy.name, data=data)
    
    def recv_algo(self, connection, recv_func):
        CRLF = constants.CRLF
        
        lines = []
        data = ''
        
        content_length = 0
        
        while True:
            new_data = recv_func(connection, 4096)
            
            data += new_data
            
            if CRLF in data:
                split_data = data.split(CRLF)
                lines.extend(split_data[:-1])
                data = split_data[-1]
            
            if lines and content_length is None:
                for line in lines:
                    try:
                        header, val = line.split(': ')
                        if header.lower() == 'content-length':
                            content_length = int(val)
                            break
                    except ValueError:
                        pass
            
            if content_length == 0 and len(lines) > 1:
                break
            
            if len(lines) > 3 and lines[-1] == '' and lines[-2] == '':
                # needs length of body, minus already fetched data
                data += clientsocket.recv(connection, (2+content_length)-len(data))
                break
        
        if data:
            data = CRLF + data
        data = CRLF.join(lines) + data
        
        try:
            headers, body = data.split(constants.CRLF+constants.CRLF)
        except ValueError:
            headers = data
            body = ''
        
        headers = headers.split(constants.CRLF)
        first_line = headers[0]
        headers = headers[1:]
        
        headers = [header.split(': ') for header in headers]
        return first_line, headers, body
    
    
    def get_request(self, connection):
        first_line, headers, body = self.recv_algo(connection, self.server_recv)
        
        method, path = first_line.split(' ', 1)
        
        return Request(method, path, headers, body)
    
    def send_response(self, connection, obj, raised=False):
        data = pickle.dumps(obj)
        
        msg = ['200 OK' if not raised else '400 Error']
        msg.append(constants.CRLF)
        
        msg.append('Content-Length: {}'.format(len(data)))
        msg.append(constants.CRLF)
        
        if data:
            msg.append(constants.CRLF)
            msg.append(data)
        
        msg = ''.join(msg)
        
        self.server_send(connection, msg)
    
    def get_response(self, connection):
        first_line, headers, body = self.recv_algo(connection, self.client_recv)
        
        status = int(first_line.split()[0])
        
        return Response(status, headers, body)
    
    def run_cmd(self, command_string):
        connection = self.client_get_connection()
        
        subprocess = ClientProxy(self, connection, Proxy('subprocess'))
        
        process = subprocess.Popen(command_string)
        
        stdout, stderr = process.communicate()
        
        returncode = process.returncode
        
        return process, stdout, stderr, returncode

