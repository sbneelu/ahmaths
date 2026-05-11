"""Phusion Passenger entry point."""
import sys
import os
import traceback

ERROR_LOG = os.path.join(os.path.dirname(__file__), 'passenger_wsgi_error.log')

try:
    from app import app as application
except Exception:
    with open(ERROR_LOG, 'a') as f:
        f.write('--- passenger_wsgi import failed ---\n')
        traceback.print_exc(file=f)
    raise
