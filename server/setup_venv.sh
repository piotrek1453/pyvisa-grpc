#!/usr/bin/sh

if [ -d "venv" ]; then
  exit 0
fi

python3 -m virtualenv venv
. ./venv/bin/activate
pip install -r requirements.txt
