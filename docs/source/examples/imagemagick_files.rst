ImageMagick files
=================

This example uses the `ImageMagick <https://imagemagick.org/>`_ tool to create an animated GIF from a sequence of image files. In addition to the ImageMagick tool, this example also requires a `RabbitMQ <https://www.rabbitmq.com>`_ message broker. The command shown below will install and run RabbitMQ using Docker:

.. code-block:: bash

   # Install and run RabbitMQ 3.13
   docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.13-management

The Python script for this example is shown below.

.. literalinclude:: ../../../examples/imagemagick_files.py

While RabbitMQ is running in a separate terminal session, use the commands shown here to start the zambeze agent then run the example script. This will create an animated GIF named ``a.gif`` in your home directory.

.. code-block:: bash

   # Start the zambeze agent
   zambeze start

   # Run the example script
   python imagemagick_files.py

   # Stop the zambeze agent
   zambeze stop

Below is a demo of running this example in the provided conda environment. Note that RabbitMQ is running on the computer where this demo was recorded.

.. raw:: html

   <script src="https://asciinema.org/a/YLZVt3d7BivkS4cPniURhURW4.js" id="asciicast-YLZVt3d7BivkS4cPniURhURW4" async="true"></script>
