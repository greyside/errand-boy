from errand_boy import constants


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


def get_command_transfer_data(cmd):
    result = commands[cmd]
    return ''.join([constants.STDOUT_PREFIX+stdout+constants.STDERR_PREFIX+stderr for stdout, stderr in result[0]]) + '\r\n\r\n' + str(result[1]) + '\r\n\r\n'


def get_command_data(cmd):
    result = commands[cmd]
    
    stdout, stderr = zip(*result[0])
    
    return ''.join(stdout), ''.join(stderr), result[1]
