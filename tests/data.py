import collections
import pickle

from errand_boy import constants
from errand_boy.transports import base


commands = {
    'cat /dev/null': ([("", "",)], 0),
    'ls -al': ([("""total 96
drwxrwxr-x  5 me me 4096 Aug  5 10:50 .
drwxrwxr-x 11 me me 4096 Mar 28 15:40 ..
drwxrwxr-x  3 me me 4096 Jan 27  2014 errand_boy
drwxrwxr-x  8 me me 4096 Aug  4 19:45 .git
-rw-rw-r--  1 me me  315 Jan 20  2014 .gitignore
-rw-rw-r--  1 me me 1482 Jan 20  2014 LICENSE
-rw-rw-r--  1 me me 1972 Jan 27  2014 README.rst
-rwxrwxr-x  1 me me 1171 Mar  3 02:29 setup.py
drwxrwxr-x  2 me me 4096 Aug  5 10:48 tests
-rw-rw-r--  1 me me  166 Jan 27  2014 .travis.yml""", "",)], 0),
}


def get_command_data(cmd):
    result = commands[cmd]
    
    stdout, stderr = zip(*result[0])
    
    return ''.join(stdout), ''.join(stderr), result[1]

def get_req(method, path, obj=None):
    if obj is not None:
        try:
            obj[1] = collections.OrderedDict(sorted(obj[1].items(), key=lambda t: t[0]))
        except:
            pass
        
        obj = pickle.dumps(obj)
        
        return ("%s %s\r\nContent-Length: %s\r\n\r\n" % (method, path, len(obj))).encode('utf-8') + obj
    else:
        return ("%s %s\r\nContent-Length: 0\r\n" % (method, path,)).encode('utf-8')

def get_resp(status, obj=None):
    if obj is not None:
        try:
            obj[1] = collections.OrderedDict(sorted(obj[1].items(), key=lambda t: t[0]))
        except:
            pass
        
        obj = pickle.dumps(obj)
        
        return ("%s\r\nContent-Length: %s\r\n\r\n" % (status, len(obj))).encode('utf-8') + obj
    else:
        return ("%s\r\nContent-Length: 0\r\n" % (status,)).encode('utf-8')

