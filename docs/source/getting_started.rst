Getting Started
===============

In order to set up and start using Zambeze, you will need the following dependencies:
 * A running rabbitmq server, see `rabbitmq documentation <https://www.rabbitmq.com/documentation.html>`_. RabbitMQ does not need admin privileges to install and run on Linux systems.
 * Python >= 3.9. We suggest using `Anaconda <https://www.anaconda.com>`_.
 * (Optional) ImageMagick to try a first mock example use-case. It is available `here <https://imagemagick.org/>`_.

Installing and Testing Zambeze 
------------------------------

1. Checkout or Download the latest release from the `Github <https://github.com/ORNL/zambeze>`_.
2. From the terminal in the zambeze directory run the following:
   
   `pip install -e .`

3. Ensure that you have a RabbitMQ server is running and you are able to reach it. You may verify this by telnet'ing the rabbitmq server like so:
   
   `telnet <rabbitmq.server> 5672`

4. Navigate to the examples directory and run the python program `imagemagick_files.py` like so:

   `python3 imagemagick_files.py`
   
   If all goes well, the command will finish with no errors and you will see a new file called `a.gif` in your home directory.


