#!/bin/bash
# Script to start the DataDivas website for Linux

# go to project folder
cd "$(dirname "$0")/DataDivas/Sonja/Website" || exit 1

# start docker environment
docker compose up --build
