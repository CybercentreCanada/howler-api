#!/bin/bash -ex

# Get version
version=$( (cd .. && poetry version --short))

# Clean build dir
(cd .. && python setup.py clean --all && rm -rf dist)

# Build wheel
(cd .. && python setup.py bdist_wheel)

# Build container
(cd .. && docker build --build-arg version=$version --no-cache -f docker/Dockerfile -t cccs/howler-api:latest -t cccs/howler-api:$version .)
