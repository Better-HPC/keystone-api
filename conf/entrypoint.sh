#!/bin/sh

# Ensure all processes terminate when the container exits
set -e
trap "kill 0" INT TERM

nginx -g 'daemon off;' -e /app/nginx/nginx.log &  # Start nginx in the background
exec keystone-api "$@"  # Redirect commands to Keystone CLI
