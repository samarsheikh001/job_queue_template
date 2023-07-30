#!/bin/bash

docker run --gpus all --env-file .env.production getrektx/sdxl-dreambooth-worker:latest