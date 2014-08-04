import collections
import json
import logging
import multiprocessing
import subprocess
import socket
from .. import __version__

logger = logging.getLogger(__name__)

try:
    from setproctitle import getproctitle, setproctitle
except ImportError:
    getproctitle = lambda: ''
    setproctitle = lambda title: None


class ProcessResult(collections.namedtuple('ProcessResult', ['VERSION', 'command_string', 'returncode', 'stdout', 'stderr'])):
    """
    VERSION - The version of the server this command was run on.
    command_string - The command that was run.
    returncode - The return code of the process.
    stdout - The stdout of the process.
    stderr - The stderr of the process.
    """
    def to_json(self, *args, **kwargs):
        return json.dumps(self._asdict(), *args, **kwargs)

class PopenProxy(object):
    returncode = None
    
    def __init__(self, transport, args):
        self._transport = transport
        self._args = args
        
        self.connection = self._transport.client_get_connection()
        
        self._transport.client_send(self.connection, args)
    
    def communicate(self, input=None):
        if self.returncode is not None:
            raise Exception('Already Returned')
        
        input = input or ''
        
        self._transport.client_send(self.connection, input)
        
        data = self._transport.client_receive(self.connection)
        
        # check for separator, if present set self.returncode
        data, returncode = self._transport.split_data(data)
        
        if returncode:
            self.returncode = int(returncode)
            self._transport.client_close(self.connection)
        
        stdout = []
        stderr = []
        
        for stdoutline in data.split(self._transport.STDOUT_PREFIX):
            stdout_split = stdoutline.split(self._transport.STDERR_PREFIX)
            
            stdout.append(stdout_split[0])
            
            stderr.extend(stdout_split[1:])
        
        stdout = ''.join(stdout)
        stderr = ''.join(stderr)
        
        return stdout, stderr


def worker_initializer(*args):
    name = multiprocessing.current_process().name
    setproctitle('errand-boy worker process %s' % name.split('-')[1])


def worker(self, connection):
    #logging.debug('worker: %s' % connection)
    return self.server_handle_client(connection)


class BaseTransport(object):
    """
    Base class providing functionality common to all transports.
    """
    SEPARATOR = '\r\n\r\n'
    STDOUT_PREFIX = '0:'
    STDERR_PREFIX = '1:'
    
    def __init__(self, pool_size=10):
        self.pool_size = pool_size
    
    def server_get_connection(self):
        pass
    
    def server_receive(self, connection):
        pass
    
    def server_send(self, connection, data):
        pass
    
    def server_send_returncode(self, connection, data):
        pass
    
    def server_send_stdout_stderr(self, connection, stdout, stderr):
        self.server_send(connection, self.STDOUT_PREFIX+stdout)
        self.server_send(connection, self.STDERR_PREFIX+stderr)
    
    def server_send_returncode(self, connection, returncode):
        self.server_send(connection, self.SEPARATOR+str(returncode))
    
    def server_close(self, connection):
        pass
    
    def split_data(self, data):
        data = data.split(self.SEPARATOR, 1)
        remainder = ''
        
        if len(data) > 1:
            data, remainder = data
        else:
            data = data[0]
        
        return data, remainder
    
    def server_handle_client(self, connection):
        #logging.debug('server_handle_client %s' % connection)
        connection = self.server_deserialize_connection(connection)
        #logging.debug('deserialized connection: %s' % connection)
        
        command_string, remainder = self.split_data(self.server_receive(connection))
        #logging.debug('received command string: %s' % command_string)
        
        process = subprocess.Popen(
            command_string,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            close_fds=True
        )
        
        while process.returncode is None:
            process_input, remainder = self.split_data(remainder+self.server_receive(connection))
            process_input = process_input or None
            print process_input
            process_stdout, process_stderr = process.communicate(input=process_input)
            
            self.server_send_stdout_stderr(connection, process_stdout, process_stderr)
        
        self.server_send_returncode(connection, process.returncode)
        
        self.server_close(connection)
    
    def server_accept(self, connection):
        pass
    
    def server_deserialize_connection(self, connection):
        return connection
    
    def server_serialize_connection(self, connection):
        return connection
    
    def run_server(self, max_accepts=1000):
        setproctitle('errand-boy master process')
        
        serverconnection = self.server_get_connection()
        
        logger.info('Accepting connections: %r' % (serverconnection,))
        
        pool = multiprocessing.Pool(self.pool_size, worker_initializer)
        
        connections = []
        
        while max_accepts:
            connection = self.server_accept(serverconnection)
            
            logger.info('Accepted connection from: %r' % (connection,))
            
            result = pool.apply_async(worker, [self, self.server_serialize_connection(connection)])
            
            connection = None
            
            max_accepts -= 1
    
    def client_get_connection(self):
        pass
    
    def client_send(self, connection, command_string):
        pass
    
    def client_receive(self, connection):
        pass
    
    def client_close(self, connection):
        pass
    
    def run_cmd(self, command_string):
        process = self.Popen(command_string)
        
        stdout = ''
        stderr = ''
        
        while process.returncode is None:
            data = process.communicate()
            stdout += data[0]
            stderr += data[1]
        
        result = ProcessResult(
            __version__,
            command_string,
            process.returncode,
            stdout,
            stderr,
        )
        
        return result
    
    def Popen(self, args):
        return PopenProxy(self, args)

