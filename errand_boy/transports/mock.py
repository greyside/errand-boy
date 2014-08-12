import eventlet

from .base import BaseTransport
from .. import constants


class MockTransport(BaseTransport):
    """
    Usage:
    
    transport = MockTransport()
    
    process, stdout, stderr = transport.run_cmd('ls -al')
    """
    def __init__(self, **kwargs):
        super(MockTransport, self).__init__(**kwargs)
    
    def server_get_connection(self):
        return None
    
    def server_recv(self, connection, l):
        in_conn, out_conn = connection
        eventlet.sleep(0)
        
        return in_conn.pop(0)
    
    def server_send(self, connection, data):
        in_conn, out_conn = connection
        out_conn.append(data)
    
    def server_accept(self, connection):
        self.connection = list(), list()
        return self.connection
    
    def run_server(self, max_accepts=1000):
        return
    
    def client_get_connection(self):
        return self.connection
    
    def client_send(self, connection, data):
        in_conn, out_conn = connection
        in_conn.append(data)
    
    def client_recv(self, connection, l):
        in_conn, out_conn = connection
        eventlet.sleep(0)
        
        return out_conn.pop(0)
    
    def run_cmd(self, command_string):
        connection = self.server_accept(None)
        
        eventlet.spawn(self.server_handle_client, connection)
        
        ret = eventlet.spawn(super(MockTransport, self).run_cmd, command_string)
        
        return ret.wait()
        
