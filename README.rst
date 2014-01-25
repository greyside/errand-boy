==========
errand-boy
==========

----------------
What does it do?
----------------

Uses Python multiprocessing to maintain a pool of worker processes used to execute arbitrary terminal commands.

-------------------------------
Why not use subprocess.Popen()?
-------------------------------

Under the hood subprocess.Popen() uses os.fork(), which copies the currently running process' memory before launching the command you want to run. If your process uses a lot of memory, such as a Celery worker using an eventlet pool, this can cause a "Cannot allocate memory" error.

errand-boy still uses subprocess.Popen(), but tries to keep a low memory footprint.

Further reading:
http://stackoverflow.com/a/13329386/241955
http://stackoverflow.com/a/14942111/241955

http://stackoverflow.com/questions/18414020/memory-usage-keep-growing-with-pythons-multiprocessing-pool

-----
Usage
-----

Run tests::

    cd errand-boy/
    python -m unittest discover

Run server::

    python -m errand_boy.run server

Run client (useful for testing/debugging)::

    python -m errand_boy.run 'ls -al'

Use the client in your code::

    from errand_boy.transports.unixsocket import UNIXSocketTransport
    
    transport = UNIXSocketTransport()
    
    result = transport.run_cmd('ls -al')
    
    print result.returncode
    print result.stdout
    print result.stderr

--------------------------------
Does it work in other languages?
--------------------------------

It shouldn't be too diffcult to write client libraries in other languages. You just need to:

1. Establish a connection to the server's socket.
2. Send the command you wish to execute as a string followed by ``\r\n\r\n`` (CRLFCRLF).
3. Receive data back from the connection until the server stops sending back data. The server will close the connection when it's done.
4. JSON decode the data, which contains stdout, stderr, and the return code.

