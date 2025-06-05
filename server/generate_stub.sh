#!/usr/bin/env bash
# This script generates Python gRPC stubs from the proto file.
set -e

. ./venv/bin/activate

# Ensure the grpcio-tools package is installed
if ! python -c "import grpc_tools" &>/dev/null; then
  echo "grpcio-tools is not installed. Installing..."
  pip install grpcio-tools
fi
# Generate the gRPC stubs

python -m grpc_tools.protoc -I../protos --python_out=. --pyi_out=. --grpc_python_out=. ../protos/pyvisa_grpc.proto
