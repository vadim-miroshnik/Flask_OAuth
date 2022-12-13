#!/bin/bash
set -exv
wait_for.sh "${POSTGRES__HOST}:5432"
flask db upgrade
python3 app_init.py
gunicorn wsgi_app:app --workers 4 --worker-class gevent --bind 0.0.0.0:8000