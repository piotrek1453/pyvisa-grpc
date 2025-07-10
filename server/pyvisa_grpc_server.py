#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import argparse
import logging
from pprint import pformat
import yaml
from concurrent import futures
import grpc
from grpc_reflection.v1alpha import reflection
import pyvisa
import pyvisa_grpc_pb2
import pyvisa_grpc_pb2_grpc


# ANSI color codes
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"
    LIGHT_RED = "\033[91m"
    LIGHT_GREEN = "\033[92m"
    LIGHT_YELLOW = "\033[93m"
    LIGHT_BLUE = "\033[94m"
    LIGHT_MAGENTA = "\033[95m"
    LIGHT_CYAN = "\033[96m"
    LIGHT_WHITE = "\033[97m"


# Custom formatter with colors
class ColoredFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: Colors.GRAY
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + Colors.RESET,
        logging.INFO: Colors.LIGHT_CYAN
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + Colors.RESET,
        logging.WARNING: Colors.LIGHT_YELLOW
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + Colors.RESET,
        logging.ERROR: Colors.LIGHT_RED
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + Colors.RESET,
        logging.CRITICAL: Colors.BOLD
        + Colors.LIGHT_RED
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + Colors.RESET,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# Configure logging with colors
def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredFormatter())
    logging.basicConfig(level=logging.DEBUG, handlers=[handler])


setup_logging()
logger = logging.getLogger("PyVISAService")


# Colorized pformat wrapper
def cformat(obj, color=Colors.LIGHT_WHITE):
    if isinstance(obj, Exception):
        return f"{color}{str(obj)}{Colors.RESET}"
    return f"{color}{pformat(obj)}{Colors.RESET}"


class PyVISAService(pyvisa_grpc_pb2_grpc.PyVISAServiceServicer):
    def __init__(self):
        super().__init__()
        self.open_resources = {}  # {resource_name: resource_object}
        try:
            logger.debug("Initializing VISA Resource Manager")
            self.rm = pyvisa.ResourceManager("@py")
            logger.info(
                f"{Colors.GREEN}VISA Resource Manager initialized{Colors.RESET}"
            )
            self.available_resources = self.rm.list_resources()
            logger.info(
                f"{Colors.GREEN}Detected VISA resources:\n{cformat(self.available_resources, Colors.GREEN)}{Colors.RESET}"
            )
        except Exception as e:
            logger.error(
                f"{Colors.RED}Failed to initialize VISA Resource Manager: {e}{Colors.RESET}"
            )
            raise

    def ListResources(self, request, context):
        """List available instruments"""
        try:
            self.available_resources = self.rm.list_resources()
            logger.info(f"{Colors.GREEN}Available resources:\n{Colors.RESET}")
            for res in self.available_resources:
                yield pyvisa_grpc_pb2.ListResourcesResponse(
                    resource_name=res,
                    status=pyvisa_grpc_pb2.StatusResponse(
                        success=True, message=""
                    ),
                )
        except Exception as e:
            yield pyvisa_grpc_pb2.ListResourcesResponse(
                resource_name="",
                status=pyvisa_grpc_pb2.StatusResponse(
                    success=False, message=f"Exception:\n{e}"
                ),
            )

    def Connect(self, request, context):
        """Connect to a VISA resource"""
        try:
            if request.resource_name in self.open_resources:
                return pyvisa_grpc_pb2.StatusResponse(
                    success=True,
                    message=f"Already connected to {request.resource_name}",
                )

            resource = self.rm.open_resource(request.resource_name)
            self.open_resources[request.resource_name] = resource
            logger.info(
                f"{Colors.GREEN}Connected to {request.resource_name}{Colors.RESET}"
            )

            return pyvisa_grpc_pb2.StatusResponse(
                success=True, message=f"Connected to {request.resource_name}"
            )
        except Exception as e:
            error_msg = (
                f"Failed to connect to {request.resource_name}: {str(e)}"
            )
            logger.error(f"{Colors.RED}{error_msg}{Colors.RESET}")
            return pyvisa_grpc_pb2.StatusResponse(
                success=False, message=error_msg
            )

    def Disconnect(self, request, context):
        """Disconnect from a VISA resource"""
        try:
            if request.resource_name not in self.open_resources:
                return pyvisa_grpc_pb2.StatusResponse(
                    success=True,
                    message=f"Not connected to {request.resource_name}",
                )

            resource = self.open_resources.pop(request.resource_name)
            resource.close()
            logger.info(
                f"{Colors.GREEN}Disconnected from {request.resource_name}{Colors.RESET}"
            )

            return pyvisa_grpc_pb2.StatusResponse(
                success=True,
                message=f"Disconnected from {request.resource_name}",
            )
        except Exception as e:
            error_msg = (
                f"Error disconnecting from {request.resource_name}: {str(e)}"
            )
            logger.error(f"{Colors.RED}{error_msg}{Colors.RESET}")
            return pyvisa_grpc_pb2.StatusResponse(
                success=False, message=error_msg
            )

    def Read(self, request, context):
        """Read from a VISA resource"""
        try:
            if request.resource_name not in self.open_resources:
                error_msg = f"Not connected to {request.resource_name}"
                logger.error(f"{Colors.RED}{error_msg}{Colors.RESET}")
                return pyvisa_grpc_pb2.ReadResponse(
                    status=pyvisa_grpc_pb2.StatusResponse(
                        success=False, message=error_msg
                    )
                )

            resource = self.open_resources[request.resource_name]
            data = resource.read()
            logger.debug(f"Read from {request.resource_name}: {data}")

            return pyvisa_grpc_pb2.ReadResponse(
                data=data, status=pyvisa_grpc_pb2.StatusResponse(success=True)
            )
        except Exception as e:
            error_msg = f"Error reading from {request.resource_name}: {str(e)}"
            logger.error(f"{Colors.RED}{error_msg}{Colors.RESET}")
            return pyvisa_grpc_pb2.ReadResponse(
                status=pyvisa_grpc_pb2.StatusResponse(
                    success=False, message=error_msg
                )
            )

    def Write(self, request, context):
        """Write to a VISA resource"""
        try:
            if request.resource_name not in self.open_resources:
                error_msg = f"Not connected to {request.resource_name}"
                logger.error(f"{Colors.RED}{error_msg}{Colors.RESET}")
                return pyvisa_grpc_pb2.StatusResponse(
                    success=False, message=error_msg
                )

            resource = self.open_resources[request.resource_name]
            resource.write(request.data)
            logger.debug(f"Wrote to {request.resource_name}: {request.data}")

            return pyvisa_grpc_pb2.StatusResponse(
                success=True,
                message=f"Data written to {request.resource_name}",
            )
        except Exception as e:
            error_msg = f"Error writing to {request.resource_name}: {str(e)}"
            logger.error(f"{Colors.RED}{error_msg}{Colors.RESET}")
            return pyvisa_grpc_pb2.StatusResponse(
                success=False, message=error_msg
            )

    def Query(self, request, context):
        """Query a VISA resource (write then read)"""
        try:
            if request.resource_name not in self.open_resources:
                error_msg = f"Not connected to {request.resource_name}"
                logger.error(f"{Colors.RED}{error_msg}{Colors.RESET}")
                return pyvisa_grpc_pb2.ReadResponse(
                    status=pyvisa_grpc_pb2.StatusResponse(
                        success=False, message=error_msg
                    )
                )

            resource = self.open_resources[request.resource_name]
            data = resource.query(request.command)
            logger.debug(
                f"Query {request.resource_name}: {request.command} -> {data}"
            )

            return pyvisa_grpc_pb2.ReadResponse(
                data=data, status=pyvisa_grpc_pb2.StatusResponse(success=True)
            )
        except Exception as e:
            error_msg = f"Error querying {request.resource_name}: {str(e)}"
            logger.error(f"{Colors.RED}{error_msg}{Colors.RESET}")
            return pyvisa_grpc_pb2.ReadResponse(
                status=pyvisa_grpc_pb2.StatusResponse(
                    success=False, message=error_msg
                )
            )


def load_config(config_path="config.yaml"):
    """Load configuration from YAML file"""
    default_config = {
        "server": {
            "port": 50051,
            "ssl": False,
            "ssl_key": "certs/server.key",
            "ssl_cert": "certs/server.pem",
            "log_level": "DEBUG",
        }
    }

    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}

            # Deep merge with default config
            def deep_update(d, u):
                for k, v in u.items():
                    if isinstance(v, dict):
                        d[k] = deep_update(d.get(k, {}), v)
                    else:
                        d[k] = v
                return d

            return deep_update(default_config, config)
        except Exception as e:
            logger.warning(
                f"{Colors.YELLOW}Error loading config file:\n{cformat(str(e), Colors.LIGHT_YELLOW)}\nUsing defaults.{Colors.RESET}"
            )
    return default_config


def parse_args():
    """Parse command line arguments"""
    config = load_config()
    server_config = config.get("server", {})

    parser = argparse.ArgumentParser(description="PyVISA gRPC Server")
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to config file (default: config.yaml)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=server_config.get("port", 50051),
        help="Server port (default: 50051)",
    )
    parser.add_argument(
        "--ssl",
        action="store_true",
        default=server_config.get("ssl", False),
        help="Enable HTTPS (default: false)",
    )
    parser.add_argument(
        "--ssl-key",
        type=str,
        default=server_config.get("ssl_key", "certs/server.key"),
        help="Path to SSL key (default: certs/server.key)",
    )
    parser.add_argument(
        "--ssl-cert",
        type=str,
        default=server_config.get("ssl_cert", "certs/server.pem"),
        help="Path to SSL certificate (default: certs/server.pem)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=server_config.get("log_level", "DEBUG"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: DEBUG)",
    )
    return parser.parse_args()


def get_server_credentials(ssl_key_path, ssl_cert_path):
    """Load SSL credentials for secure connection"""
    try:
        with open(ssl_key_path, "rb") as f:
            private_key = f.read()
        with open(ssl_cert_path, "rb") as f:
            certificate = f.read()
        return grpc.ssl_server_credentials([(private_key, certificate)])
    except Exception as e:
        logger.error(
            f"{Colors.RED}SSL certificate loading error:\n{cformat(str(e), Colors.LIGHT_RED)}{Colors.RESET}"
        )
        raise


def serve():
    args = parse_args()

    # Reconfigure logging with the specified level
    logger.setLevel(args.log_level)
    for handler in logger.handlers:
        handler.setLevel(args.log_level)

    logger.info(
        f"{Colors.LIGHT_CYAN}Starting server with configuration:\n{cformat(vars(args), Colors.LIGHT_BLUE)}{Colors.RESET}"
    )

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service = PyVISAService()
    pyvisa_grpc_pb2_grpc.add_PyVISAServiceServicer_to_server(service, server)

    # Enable reflection
    SERVICE_NAMES = (
        pyvisa_grpc_pb2.DESCRIPTOR.services_by_name["PyVISAService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    try:
        if args.ssl:
            credentials = get_server_credentials(args.ssl_key, args.ssl_cert)
            server.add_secure_port(f"[::]:{args.port}", credentials)
            logger.info(
                f"{Colors.GREEN}Server started on port {args.port} with SSL{Colors.RESET}"
            )
        else:
            server.add_insecure_port(f"[::]:{args.port}")
            logger.warning(
                f"{Colors.YELLOW}Server started on port {args.port} (INSECURE){Colors.RESET}"
            )

        server.start()
        logger.info(
            f"{Colors.GREEN}Server ready to handle requests...{Colors.RESET}"
        )
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info(f"{Colors.CYAN}Shutting down server...{Colors.RESET}")
        server.stop(0)
        logger.info(f"{Colors.CYAN}Server stopped{Colors.RESET}")
    except Exception as e:
        logger.error(
            f"{Colors.RED}Server error:\n{cformat(str(e), Colors.LIGHT_RED)}{Colors.RESET}",
            exc_info=True,
        )
        raise


if __name__ == "__main__":
    serve()
