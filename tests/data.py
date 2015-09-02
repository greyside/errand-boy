import collections
import pickle
import six
import subprocess

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
    stdout = ''.join(stdout)
    stderr = ''.join(stderr)

    returncode = result[1]

    requests = [
        get_req('GET', 'subprocess.Popen'),
        get_req('GET', 'subprocess.PIPE'),
        get_req('GET', 'subprocess.PIPE'),
        get_req('CALL', 'obj1', [(cmd,), {'shell': True, 'stderr': subprocess.PIPE, 'stdout': subprocess.PIPE}]),
        get_req('GET', 'obj2.communicate'),
        get_req('CALL', 'obj3', [tuple(), {}]),
        get_req('GET', 'obj4.__iter__'),
        get_req('CALL', 'obj5', [tuple(), {}]),
        get_req('GET', 'obj6.next' if six.PY2 else 'obj6.__next__'),
        get_req('CALL', 'obj7', [tuple(), {}]),
        get_req('CALL', 'obj7', [tuple(), {}]),
        get_req('CALL', 'obj7', [tuple(), {}]),
        get_req('GET', 'obj2.returncode'),
        b'',
    ]

    responses = [
        get_resp('200 OK', base.RemoteObjRef('obj1')),
        get_resp('200 OK', subprocess.PIPE),
        get_resp('200 OK', subprocess.PIPE),
        get_resp('200 OK', base.RemoteObjRef('obj2')),
        get_resp('200 OK', base.RemoteObjRef('obj3')),
        get_resp('200 OK', base.RemoteObjRef('obj4')),
        get_resp('200 OK', base.RemoteObjRef('obj5')),
        get_resp('200 OK', base.RemoteObjRef('obj6')),
        get_resp('200 OK', base.RemoteObjRef('obj7')),
        get_resp('200 OK', stdout),
        get_resp('200 OK', stderr),
        get_resp('400 Error', StopIteration()),
        get_resp('200 OK', returncode),
    ]

    return cmd, stdout, stderr, returncode, requests, responses

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

data = {
    'ls -al': ('ls -al', get_command_data('ls -al')),
}
