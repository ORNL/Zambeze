Logging
=======

The Zambeze agent runs as a daemon process and logs messages to a log file. The log file records information about the agent's activities, and it can be used for debugging and monitoring. Zambeze provides a logging utility to view the log file and supports ``--mode``, ``--numlines``, and ``--follow`` options:

.. code-block:: text

    zambeze logs
    zambeze logs --mode head
    zambeze logs --mode tail --numlines 20

The logger defaults to ``tail`` mode with ``10`` lines and it doesn't support negative integers, which results in no lines logged. 

The ``--follow / -f`` option can be used for continuous monitoring while in ``tail`` mode. The utility automatically tracks the agent's logs upon restarts, ensuring that the most recent log is always available without needing to restart the logging process:

.. code-block:: text

    zambeze logs -f
    zambeze logs --mode tail --follow
    zambeze logs --mode tail --numlines 20 --follow
