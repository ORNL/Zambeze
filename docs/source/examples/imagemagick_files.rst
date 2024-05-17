ImageMagick files
=================

This example uses the `ImageMagick <https://imagemagick.org/>`_ tool to create an animated GIF from a sequence of image files. In addition to the ImageMagick tool, this example also requires a `RabbitMQ <https://www.rabbitmq.com>`_ message broker. The command shown below will install and run RabbitMQ using Docker:

.. code-block:: bash

   # Install and run RabbitMQ 3.13
   docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.13-management

The Python script for this example is shown below.

.. literalinclude:: ../../../examples/imagemagick_files.py

While RabbitMQ is running in a separate terminal, use the commands shown below to run this example in another terminal:

.. code-block:: bash

   # Start the zambeze agent
   zambeze start

   # Run the example script
   python imagemagick_files.py

   # Stop the zambeze agent
   zambeze stop
