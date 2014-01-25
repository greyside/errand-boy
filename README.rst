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

Under the hood subprocess.Popen() uses os.fork(), which copies the currently running process' memory before launching the command you want to run. If your process uses a lot of memory, such as a Celery worker using an eventlet pool, this can cause a "Cannot allocate memory" error (http://stackoverflow.com/a/13329386/241955).

errand-boy still uses subprocess.Popen(), but tries to keep a low memory footprint.

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

