import os

HOST = os.getenv('HOST', "127.0.0.1")
NATS_HOST = os.getenv('NATS_HOST', "127.0.0.1")
NATS_PORT = int(os.getenv('NATS_PORT', 4222))
