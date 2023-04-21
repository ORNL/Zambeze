"""
A file to keep all global constants and settings, particularly environment vars.
"""
import os

# This is the hostname of THIS service.
HOST = os.getenv("HOST", "127.0.0.1")

# Hostname and port of the NATS queueing system
NATS_HOST = os.getenv("NATS_HOST", "127.0.0.1")
NATS_PORT = int(os.getenv("NATS_PORT", 4222))

# Hostname and port of the RabbitMQ queueing system
RABBIT_HOST = os.getenv("RABBIT_HOST", "127.0.0.1")
RABBIT_PORT = int(os.getenv("RABBIT_PORT", 5672))

# PATHS
SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.realpath(os.path.join(SOURCE_DIR, ".."))
DB_DIR = os.path.join(PROJECT_DIR, "zambeze/db")
LOCAL_DB_FILE = os.path.join(DB_DIR, "zambeze.db")
LOCAL_DB_SCHEMA = os.path.join(DB_DIR, "zambeze_schema.sql")
