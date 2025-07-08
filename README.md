# pyvisa-grpc

A simple GRPC server running pyvisa-py so that you can control measurement
instruments without the need to use humungous, closed-source implementations of
VISA using your favourite programming language as long as it supports gRPC.

# Running the server

Server parses config from server/config.yaml. By default it runs without
encryption on port 50051.

Most tasks needed for development and usage are handled by justfile located in
server/ directory (need to cd into it to run the script).

For running the server you can run

```
just run
```

For easy setup of self-signed SSL

```
just ssl-generate
```

and change ssl parameter value to true in server/config.yaml.

# TODO

- Add method to list available resources.
