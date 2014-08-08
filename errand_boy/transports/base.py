import logging
import multiprocessing
import signal
import subprocess
import sys

from .. import constants
from .. import __version__


logger = logging.getLogger(__name__)

try:
    from setproctitle import setproctitle
except ImportError:
    logger.info('Cannot set process name.')
    setproctitle = lambda title: None


class PopenProxy(object):
    def __init__(self, transport, args):
        self._transport = transport
        self._args = args
        
        self.stdin = None
        self.stdout = None
        self.stderr = None
        self.pid = None
        self.returncode = None
        
        self.connection = self._transport.client_get_connection()
        
        self._transport.client_send(self.connection, args)
    
    def communicate(self, input=None):
        if self.returncode is not None:
            raise Exception('Already Returned')
        
        input = input or ''
        
        self._transport.client_send(self.connection, input)
        
        data, returncode = self._transport.split_data(self._transport.client_recv(self.connection))
        
        self.returncode = int(returncode)
        self._transport.client_close(self.connection)
        
        stdout = []
        stderr = []
        
        for line in data.split(constants.STD_SEP):
            if constants.STD_ID_SEP in line:
                std_id, msg = line.split(constants.STD_ID_SEP, 1)
                if std_id == constants.STDOUT_ID:
                    stdout.append(msg)
                if std_id == constants.STDERR_ID:
                    stderr.append(msg)
        
        stdout = ''.join(stdout)
        stderr = ''.join(stderr)
        
        return stdout, stderr


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
    
    def server_send_returncode(self, connection, data):
        pass
    
    def server_send_stdout_stderr(self, connection, stdout, stderr):
        self.server_send(connection, constants.STDOUT_PREFIX+stdout)
        self.server_send(connection, constants.STDERR_PREFIX+stderr)
    
    def server_send_returncode(self, connection, returncode):
        self.server_send(connection, constants.SEP+str(returncode)+constants.SEP)
    
    def server_close(self, connection):
        pass
    
    def split_data(self, data, num=1):
        data = [s for s in data.split(constants.SEP, num) if s]
        remainder = ''
        
        if len(data) > num:
            data, remainder = data
        else:
            data = data[0]
        
        return data, remainder
    
    def server_handle_client(self, connection):
        connection = self.server_deserialize_connection(connection)
        
        logger.debug('server_handle_client: {}'.format(self.connection_to_string(connection)))
        
        command_string, process_input = self.split_data(self.server_recv(connection))
        
        logger.info('Received command string: {}'.format(command_string))
        
        process = subprocess.Popen(
            command_string,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            close_fds=True
        )
        
        process_input = process_input or None
        
        process_stdout, process_stderr = process.communicate(input=process_input)
        
        self.server_send_stdout_stderr(connection, process_stdout, process_stderr)
        
        self.server_send_returncode(connection, process.returncode)
        
        self.server_close(connection)
    
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
    
    def run_cmd(self, command_string):
        process = self.Popen(command_string)
        
        stdout, stderr = process.communicate()
        
        return process, stdout, stderr
    
    def Popen(self, args, *options, **kwargs):
        return PopenProxy(self, args)

