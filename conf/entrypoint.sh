#!/bin/bash

set -e
trap "kill 0" SIGINT SIGTERM

nginx -g 'daemon off;' & # start nginx in background
exec keystone-api "$@" # Redirect commands to Keystone CLI
