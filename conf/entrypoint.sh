#!/bin/sh

# Ensure all processes are killed when the container terminates
set -e
trap "kill 0" INT TERM

nginx  # Start nginx in background
exec keystone-api "$@"  # Redirect commands to Keystone CLI
