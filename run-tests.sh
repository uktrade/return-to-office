#!/bin/bash

set -e

docker-compose run --rm web pytest --tb=short "$@"
