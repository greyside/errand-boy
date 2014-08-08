import argparse
import importlib
import logging
import logging.config
import sys

from . import __version__


parser = argparse.ArgumentParser(description='Start errand-boy.')
parser.add_argument('-t', '--transport', dest='transport', nargs='?',
           default='errand_boy.transports.unixsocket.UNIXSocketTransport',
           help='Python path to the transport to use.')
parser.add_argument('--pool-size', dest='pool_size', nargs='?', type=int,
           default=1000,
           help='Number of worker processes to use.')
parser.add_argument('--max-accepts', dest='max_accepts', nargs='?', type=int,
           default=1000,
           help='Max number of connections the server will accept.')
parser.add_argument('command', nargs=argparse.REMAINDER)
parser.add_argument('--version', action='version', version=__version__)

class MaxLevelFilter(logging.Filter):
    def __init__(self, level):
        self._level = level

    def filter(self, rec):
        return rec.levelno <= self._level

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'stdout': {
            '()': MaxLevelFilter,
            'level': 'WARNING',
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(process)d %(thread)d %(name)s:%(lineno)s %(funcName)s() %(message)s'
        },
    },
    'handlers': {
        'stdout': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'verbose',
        },
        'stderr': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'stream': sys.stderr,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'errand_boy': {
            'handlers': ['stderr', 'stdout'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

def main(argv):
    parsed_args = parser.parse_args(argv[1:])
    
    mod, klass = parsed_args.transport.rsplit('.', 1)
    
    transport = getattr(importlib.import_module(mod), klass)()
    
    command = parsed_args.command
    
    if not command:
        logging.config.dictConfig(LOGGING)
        
        transport.run_server(
            pool_size=parsed_args.pool_size,
            max_accepts=parsed_args.max_accepts
        )
    else:
        process, stdout, stderr = transport.run_cmd(' '.join(command))
        
        sys.stdout.write(stdout)
        sys.stderr.write(stderr)
        
        sys.exit(process.returncode)

if __name__ == '__main__':
    main(sys.argv)

