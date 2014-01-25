import collections
import json
import subprocess

from .. import __version__

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

class BaseTransport(object):
    """
    Usage:
    
    cmd = 'ls -al'
    
    transport = UNIXSocketTransport()
    
    # returns ProcessResult instance.
    result = transport.run_cmd(cmd)
    """
    
    def server_run_process(self, command_string):
        print 'Executing: %s' % command_string
        
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
        command_string = self.server_receive(connection)
        
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
    
    def run_server(self, max_accepts=1000):
        serverconnection = self.server_get_connection()
        
        print 'Accepting connections: %r' % serverconnection
        
        while max_accepts:
            connection = self.server_accept(serverconnection)
            
            print 'Accepted connection from: %r' % (connection,)
            
            self.server_handle_client(connection)
            
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

