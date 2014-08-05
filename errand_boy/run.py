import sys


def main(argv):
    from .transports.unixsocket import UNIXSocketTransport
    
    transport = UNIXSocketTransport()
    
    if len(argv) == 1:
        transport.run_server()
    else:
        process, stdout, stderr = transport.run_cmd(' '.join(argv[1:]))
        
        sys.stdout.write(stdout)
        sys.stderr.write(stderr)
        
        sys.exit(process.returncode)

if __name__ == '__main__':
    main(sys.argv)

