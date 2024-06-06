Logging
=======

The Zambeze agent runs as a daemon process and logs messages to a log file. The log file records information about the agent's activities, and it can be used for debugging and monitoring.
Zambeze provides a logging utility to view the log file and supports ``--mode``, ``--numlines``, and ``--follow`` options:

.. code-block:: text

    zambeze logs
    zambeze logs --mode head
    zambeze logs --mode tail --numlines 20

Defaults to ``tail`` mode with ``10`` lines. Doesn't support negative integers, which results in no lines logged. 

The ``--follow / -f`` option can be used for continuous monitoring while in ``tail`` mode:

.. code-block:: text

    zambeze logs --f
    zambeze logs --mode tail --follow
    zambeze logs --mode tail --numlines 20 --follow
