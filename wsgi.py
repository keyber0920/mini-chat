# passenger_wsgi.py
import sys
import os

# Loyiha yo'li
path = '/home/shaxao08/mini-chat'
if path not in sys.path:
    sys.path.append(path)

from app import create_app

# WSGI application obyekti
application = create_app()