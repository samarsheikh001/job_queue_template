#!/bin/bash

celery -A app.celery worker --loglevel INFO --pool solo -c 1 -Q STANDARD_train-sdxl-dreambooth,STANDARD_inference-sdxl