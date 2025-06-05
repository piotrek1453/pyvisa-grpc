#!/usr/bin/sh

python3 -m virtualenv venv
. ./venv/bin/activate
pip install -r requirements.txt
python3 pyvisa_grpc_server.py
