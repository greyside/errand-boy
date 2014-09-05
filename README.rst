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
    
    
    errand_boy_transport = UNIXSocketTransport()
    
    stdout, stderr, returncode = errand_boy_transport.run_cmd('ls -al')
    
    print stdout
    print stderr
    print returncode

Use a subprocess.Popen-like interface::

    from errand_boy.transports.unixsocket import UNIXSocketTransport
    
    
    errand_boy_transport = UNIXSocketTransport()
    
    # Attribute accesses and function calls on objects retrieved via a session
    # result in a call to the errand-boy server, unless that object is a string
    # or number type.
    with errand_boy_transport.get_session() as session:
        subprocess = session.subprocess
        
        # Here, subprocess.Popen is actually a reference to the actual objects
        # on the errand-boy server. subprocess.PIPE is an int.
        process = subprocess.Popen('ls -al', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, close_fds=True)
        
        # Here, process_stdout and process_stderr are strings and returncode is
        # an int, so their actual values are returned instead of references to
        # the remote objects. This means it's safe to use these values later on
        # outside of the current session.
        process_stdout, process_stderr = process.communicate()
        returncode = process.returncode
    
    print stdout
    print stderr
    print returncode
    
    # Since the session has been closed, trying this will result in an error:
    print process.returncode
    # raised errand_boy.exceptions.SessionClosedError()

Run load tests::

    python -m errand_boy.run --max-accepts=0

    pip install Fabric locustio
    cd errand-boy/
    fab locust_local

--------------------------------
Does it work in other languages?
--------------------------------

The client/server use an HTTP-inspired protocol, but the data that's sent back and forth is currently serialized using Python's Pickle format. Support could be added for other serialization types though.

-----------
Development
-----------

Further reading:

* http://stackoverflow.com/questions/18414020/memory-usage-keep-growing-with-pythons-multiprocessing-pool

