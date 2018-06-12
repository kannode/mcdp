#!/bin/bash
echo "Inside mcdp_server.sh"
echo "USER $USER"
echo "UID $UID"
export HOME=/home
echo "HOME $HOME"
export COLUMNS=160
export NODE_PATH=/project/node_modules
echo "Activating virtual env"
source /project/deploy/bin/activate
echo "Now executing command $@"
mcdp-web
