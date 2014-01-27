import sys

def main(argv):
    from .transports.unixsocket import UNIXSocketTransport
    
    transport = UNIXSocketTransport()
    
    if argv[1] == 'server':
        transport.run_server()
    else:
        print transport.run_cmd(' '.join(argv[1:])).to_json(indent=4)

if __name__ == '__main__':
    main(sys.argv)

