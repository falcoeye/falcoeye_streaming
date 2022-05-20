#!/bin/sh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

source $SCRIPT_DIR/../../env/env/bin/activate
export FLASK_RUN_PORT=5000
export FLASK_APP=falcoeye
export FLASK_CONFIG=development 
cd $SCRIPT_DIR/..
flask run