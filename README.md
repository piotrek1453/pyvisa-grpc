# pyvisa-grpc

A simple GRPC server running pyvisa-py so that you can control measurement
instruments without the need to use humungous, closed-source implementations of
VISA using your favourite programming language as long as it supports gRPC.

# Running the server

Server parses config from server/config.yaml. By default it runs without
encryption on port 50051.

For easy setup of self-signed SSL certs run this command in root of the repo:

```
openssl req -x509 -newkey rsa:4096 -keyout server/certs/server.key -out server/certs/server.pem -days 365 -nodes -subj "/CN=localhost"
```

and change ssl parameter value to true in server/config.yaml.

# TODO

- Add Query() method (read+write in one),
- rethink the way of handling sessions: as of now there's one resource manager
  created for every instrument connected.
