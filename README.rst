==========
errand-boy
==========

.. image:: https://travis-ci.org/SeanHayes/errand-boy.svg?branch=master
    :target: https://travis-ci.org/SeanHayes/errand-boy
.. image:: https://coveralls.io/repos/SeanHayes/errand-boy/badge.png?branch=master
    :target: https://coveralls.io/r/SeanHayes/errand-boy?branch=master

----------------
What does it do?
----------------

Uses Python multiprocessing to maintain a pool of worker processes used to execute arbitrary terminal commands.

-------------------------------
Why not use subprocess.Popen()?
-------------------------------

Under the hood subprocess.Popen() uses os.fork(), which copies the currently running process' memory before launching the command you want to run. If your process uses a lot of memory, such as a Celery worker using an eventlet pool, this can cause a "Cannot allocate memory" error.

errand-boy still uses subprocess.Popen(), but tries to keep a low memory footprint. Your celery greenthread workers can communicate with it via asynchronous network calls.

Further reading:

#. http://stackoverflow.com/a/13329386/241955
#. http://stackoverflow.com/a/14942111/241955

-----
Setup
-----

Install:

    pip install errand-boy

    # optional
    pip install setproctitle

-----
Usage
-----

Run tests::

    cd errand-boy/
    python -m unittest discover

Run server::

    python -m errand_boy.run

Run client (useful for testing/debugging)::

    python -m errand_boy.run 'ls -al'

Use the client in your code::

    from errand_boy.transports.unixsocket import UNIXSocketTransport
    
    transport = UNIXSocketTransport()
    
    process, stdout, stderr = transport.run_cmd('ls -al')
    
    print process.returncode
    print stdout
    print stderr

Use a subprocess.Popen-like interface::

    from errand_boy.transports.unixsocket import UNIXSocketTransport
    
    transport = UNIXSocketTransport()
    
    process = transport.Popen('ls -al')
    
    stdout, stderr = process.communicate(input='foo')
    
    print process.returncode
    print stdout
    print stderr

Run load tests::

    python -m errand_boy.run --max-accepts=0

    pip install Fabric locustio
    cd errand-boy/
    fab locust_local

--------------------------------
Does it work in other languages?
--------------------------------

It shouldn't be too diffcult to write client libraries in other languages. You just need to:

1. Establish a connection to the server's socket.
2. Send the command you wish to execute as a string followed by ``\r\n\r\n``. Then send your input or an empty string followed by ``\r\n\r\n``.
3. Receive data back from the connection until the server stops sending back data. The server will close the connection when it's done.

-----------
Development
-----------

Further reading:

* http://stackoverflow.com/questions/18414020/memory-usage-keep-growing-with-pythons-multiprocessing-pool

