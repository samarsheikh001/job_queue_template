#!/bin/bash

celery -A app.celery worker --loglevel=info --hostname=custom_worker_name@%h -c 1