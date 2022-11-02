"""
A file to keep all global constants and settings, particularly environment vars.
"""
import os

# This is the hostname of THIS service.
HOST = os.getenv("HOST", "127.0.0.1")
ZMQ_PORT = int(os.getenv("ZMQ_PORT", 5555))

# Hostname and port of the NATS queueing system
NATS_HOST = os.getenv("NATS_HOST", "127.0.0.1")
NATS_PORT = int(os.getenv("NATS_PORT", 4222))


# PATHS

SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.realpath(os.path.join(SOURCE_DIR, ".."))
DB_DIR = os.path.join(PROJECT_DIR, "db")
LOCAL_DB_FILE = os.path.join(DB_DIR, "zambeze.db")
LOCAL_DB_SCHEMA = os.path.join(DB_DIR, "zambeze_schema.sql")