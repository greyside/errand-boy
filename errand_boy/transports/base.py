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
    
    def __init__(self, pool_size=10):
        self.pool_size = pool_size
    
    def server_run_process(self, command_string):
        #logging.debug('Executing: %s' % command_string)
        
        process = subprocess.Popen(
            command_string,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            close_fds=True
        )
        process_stdout, process_stderr = process.communicate()
        
        return process, process_stdout, process_stderr
    
    def server_get_connection(self):
        pass
    
    def server_receive(self, connection):
        pass
    
    def server_send(self, connection, data):
        pass
    
    def server_handle_client(self, connection):
        #logging.debug('server_handle_client %s' % connection)
        connection = self.server_deserialize_connection(connection)
        #logging.debug('deserialized connection: %s' % connection)
        
        command_string = self.server_receive(connection)
        
        #logging.debug('received command string: %s' % command_string)
        
        process, process_stdout, process_stderr = self.server_run_process(command_string)
        
        ret_data = ProcessResult(
            __version__,
            command_string,
            process.returncode,
            process_stdout,
            process_stderr,
        )
        
        ret_data = ret_data.to_json()
        
        self.server_send(connection, ret_data)
    
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
    
    def run_cmd(self, command_string):
        connection = self.client_get_connection()
        
        self.client_send(connection, command_string)
        
        data = self.client_receive(connection)
        
        data = json.loads(data)
        
        return ProcessResult(**data)

