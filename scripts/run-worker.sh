#!/bin/bash

celery -A app.celery worker --loglevel=info -c 1 -Q train-sdxl-dreambooth