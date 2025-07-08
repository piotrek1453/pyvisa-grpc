#!/usr/bin/sh

if [ -d "venv" ]; then
  . ./venv/bin/activate
  python3 pyvisa_grpc_server.py
  exit 0
fi

python3 -m virtualenv venv
. ./venv/bin/activate
pip install -r requirements.txt
python3 pyvisa_grpc_server.py
