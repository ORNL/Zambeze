Getting Started
===============

In order to set up and start using Zambeze, you will need the following dependencies:
 * A running nats server, see `nats documentation <https://docs.nats.io>`_.
 * Python >= 3.7. We suggest using `Anaconda <https://www.anaconda.com>`_.
 * (Optional) ImageMagick to try a first mock example use-case. It is available `here <https://imagemagick.org/>`_.

NATS Server Setup
------------------

.. code-block:: console

    $ curl -L https://github.com/nats-io/nats-server/releases/download/v2.8.4/nats-server-v2.8.4-linux-amd64.zip -o nats-server.zip
    $ unzip nats-server.zip
    $ sudo cp nats-server /usr/bin/

Start the nats-server as follows:

.. code-block:: console

    $ nats-server

If all goes well, a message similar to the following should appear:

.. code-block:: console

    [26982] 2022/07/26 23:42:39.928152 [INF] Starting nats-server
    [26982] 2022/07/26 23:42:39.928370 [INF]   Version:  2.8.4
    [26982] 2022/07/26 23:42:39.928378 [INF]   Git:      [66524ed]
    [26982] 2022/07/26 23:42:39.928385 [INF]   Name:     NCVC6Y3EYJEFPMO7IJGFB2ZMXMMNTPKNFRMR57FKA7FDV46R2VFWDNCF
    [26982] 2022/07/26 23:42:39.928391 [INF]   ID:       NCVC6Y3EYJEFPMO7IJGFB2ZMXMMNTPKNFRMR57FKA7FDV46R2VFWDNCF
    [26982] 2022/07/26 23:42:39.930477 [INF] Listening for client connections on 0.0.0.0:4222
    [26982] 2022/07/26 23:42:39.931565 [INF] Server is ready


Installing Zambeze 
-------------------


