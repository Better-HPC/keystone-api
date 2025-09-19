#!/bin/bash

set -e
trap "kill 0" SIGINT SIGTERM

nginx # Start nginx in background
exec keystone-api "$@" # Redirect commands to Keystone CLI
