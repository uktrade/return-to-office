production site: https://return-to-office.trade.gov.uk/

jenkins job to deploy it: https://jenkins.ci.uktrade.digital/job/return-to-office-prod/



<!-- [![circle-ci-image]][circle-ci] -->
<!-- [![codecov-image]][codecov] -->

[![image](https://circleci.com/gh/uktrade/icms/tree/master.svg?style=svg)](https://circleci.com/gh/uktrade/icms/tree/master)
[![image](https://codecov.io/gh/uktrade/icms/branch/master/graph/badge.svg)](https://codecov.io/gh/uktrade/icms)

# Return To Office

## Introduction

"Return To Office" is a system used to manage people booking desks for safely
returning to the office.

## Requirements

- [Python 3.7+](https://www.python.org/downloads/)
- [Docker Compose](https://docs.docker.com/compose/)

## Setup

## Local virtualenv

A local virtualenv is needed for a few reasons:

1. To be able to run the pre-commit checks
1. If using an IDE, so it has access to the library code and tooling

Note that the application is never actually run on the local machine while
developing, only within Docker.

## Initial setup

- `make build`
  - Build all Docker containers
- `make setup`
  - Create local virtualenv, set up pre-commit hooks, initialize database

## Running the application

Start everything using docker-compose: `make up`

Go to http://localhost:8000 and use your DIT Google account to log in.

Make sure to rebuild the Docker images if new dependencies are added to the
requirements files: `make build`.

## Code style

ICMS uses [Black](https://pypi.org/project/black/) for code formatting and
[flake8](https://flake8.pycqa.org/en/latest/) for code analysis. Useful commands:

- `make black` - Check code is formatted correctly
- `make black_format` - Reformat all code
- `make flake8` - Check code quality is up to scratch
