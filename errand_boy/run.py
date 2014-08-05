import argparse
import importlib
import sys

from . import __version__


parser = argparse.ArgumentParser(description='Start errand-boy.')
parser.add_argument('-t', '--transport', dest='transport', nargs='?',
           default='errand_boy.transports.unixsocket.UNIXSocketTransport',
           help='Python path to the transport to use.')
parser.add_argument('--max-accepts', dest='max_accepts', nargs='?', type=int,
           default=1000,
           help='Max number of connections the server will accept.')
parser.add_argument('command', nargs=argparse.REMAINDER)
parser.add_argument('--version', action='version', version=__version__)


def main(argv):
    parsed_args = parser.parse_args(argv[1:])
    
    mod, klass = parsed_args.transport.rsplit('.', 1)
    
    transport = getattr(importlib.import_module(mod), klass)()
    
    command = parsed_args.command
    
    if not command:
        transport.run_server(max_accepts=parsed_args.max_accepts)
    else:
        process, stdout, stderr = transport.run_cmd(' '.join(command))
        
        sys.stdout.write(stdout)
        sys.stderr.write(stderr)
        
        sys.exit(process.returncode)

if __name__ == '__main__':
    main(sys.argv)

