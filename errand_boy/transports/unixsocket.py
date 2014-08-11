import errno
from multiprocessing import reduction
import os
import socket

from .base import BaseTransport
from .. import constants


try:
    rebuild_socket = reduction.rebuild_socket
    reduce_socket = reduction.reduce_socket
except AttributeError:
    rebuild_socket = reduction._rebuild_socket
    reduce_socket = reduction._reduce_socket


class UNIXSocketTransport(BaseTransport):
    """
    Usage:
    
    transport = UNIXSocketTransport()
    
    process, stdout, stderr = transport.run_cmd('ls -al')
    """
    
    def __init__(self, socket_path='/tmp/errand-boy', listen_backlog=5, **kwargs):
        super(UNIXSocketTransport, self).__init__(**kwargs)
        
        self.socket_path = socket_path
        self.listen_backlog = listen_backlog
    
    def connection_to_string(self, connection):
        if isinstance(connection, tuple):
            return str((connection[0].getsockname(), connection[1],))
        return connection.getsockname()
    
    def server_get_connection(self):
        serversocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        
        try:
            os.remove(self.socket_path)
        except OSError:
            pass
        
        serversocket.bind(self.socket_path)
        serversocket.listen(self.listen_backlog)
        
        return serversocket
    
    def server_recv(self, connection, length):
        clientsocket, address = connection
        
        return clientsocket.recv(length)
    
    def server_send(self, connection, data):
        clientsocket, address = connection
        
        clientsocket.sendall(data)
    
    def server_close(self, connection):
        clientsocket, address = connection
        try:
            clientsocket.close()
        except:
            pass
    
    def server_accept(self, connection):
        return connection.accept()
    
    def server_deserialize_connection(self, connection):
        return rebuild_socket(*connection[0][1]), connection[1]
    
    def server_serialize_connection(self, connection):
        return reduce_socket(connection[0]), connection[1]
    
    def client_get_connection(self):
        clientsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        
        clientsocket.connect(self.socket_path)
        
        return clientsocket
    
    def client_send(self, connection, data):
        connection.sendall(data)
    
    def client_recv(self, connection, length):
        return connection.recv(length)
    
    def client_close(self, connection):
        try:
            connection.close()
        except:
            pass
