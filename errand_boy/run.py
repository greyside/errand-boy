import sys

if __name__ == '__main__':
    from .transports.unixsocket import UNIXSocketTransport
    
    transport = UNIXSocketTransport()
    
    if sys.argv[1] == 'server':
        transport.run_server()
    else:
        print transport.run_cmd(sys.argv[1]).to_json(indent=4)

