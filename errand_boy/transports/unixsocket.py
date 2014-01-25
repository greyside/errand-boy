import os
import socket

from .base import BaseTransport

class UNIXSocketTransport(BaseTransport):
    def __init__(self, socket_path='/tmp/errand-boy', seperator='\r\n\r\n', listen_backlog=1):
        super(UNIXSocketTransport, self).__init__()
        
        self.socket_path = socket_path
        self.seperator = seperator
        self.listen_backlog = listen_backlog
    
    def server_get_connection(self):
        serversocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        
        try:
            os.remove(self.socket_path)
        except OSError:
            pass
        
        serversocket.bind(self.socket_path)
        serversocket.listen(self.listen_backlog)
        
        return serversocket
    
    def server_receive(self, connection):
        clientsocket, address = connection
        
        data = ''
        
        while self.seperator not in data:
            new_data = clientsocket.recv(1024)
            
            data += new_data
        
        data = data.split(self.seperator, 1)[0]
        
        return data
    
    def server_send(self, connection, data):
        clientsocket, address = connection
        
        clientsocket.sendall(data)
        
        try:
            clientsocket.close()
        except:
            pass
    
    def server_accept(self, connection):
        return connection.accept()
    
    def client_get_connection(self):
        clientsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        
        clientsocket.connect(self.socket_path)
        
        return clientsocket
    
    def client_send(self, connection, command_string):
        connection.sendall(command_string+self.seperator)
    
    def client_receive(self, connection):
        data = []
        
        while True:
            new_data = connection.recv(4096)
            
            if new_data:
                data.append(new_data)
            else:
                break
        
        data = ''.join(data)
        
        try:
            clientsocket.close()
        except:
            pass
        
        return data

