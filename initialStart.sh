#!/bin/bash
# Script to start the DataDivas website for Linux

# go to project folder
cd "$(dirname "$0")/Website" || exit 1

docker compose build
# start docker environment
docker compose up
