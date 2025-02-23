import config
import json
import logging
import os
import subprocess
import socket
import sys
import time
import yaml

def receive_exact_bytes(connection, num_bytes):
    received_data = b""
    while len(received_data) < num_bytes:
        chunk = connection.recv(num_bytes - len(received_data))
        if not chunk:
            raise RuntimeError("Connection closed unexpectedly")
        received_data += chunk
    return received_data

def receive_length(connection):
    length_bytes = connection.recv(4)
    return int.from_bytes(length_bytes, byteorder='big')

def read_server_info(file_path):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            host = data.get("host")
            port = data.get("port")

            if not host or not isinstance(port, int):
                raise ValueError("Invalid host or port values in JSON file.")

            return host, port
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        logging.error(f"Failed to read {file_path}: {e}")
        sys.exit(1)

def open_vim():
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"prompt-{timestamp}.txt"
    subprocess.run(['vim', filename])
    with open(filename, 'r') as file:
        return file.read()

def find_available_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temp_socket:
        temp_socket.bind(('localhost', 0))
        return temp_socket.getsockname()[1]

def write_server_info_to_file(host, port):
    os.makedirs(config.path, exist_ok=True)
    with open(config.server_info_file, 'w') as f:
        json.dump({'host' : host, 'port' : port}, f, indent=4)

def send_response(client_socket, response):
    client_socket.sendall(len(response).to_bytes(4, 'big'))
    client_socket.sendall(response.encode())

def send_obj(client_socket, obj):
    client_socket.sendall(len(obj).to_bytes(4, 'big'))
    client_socket.sendall(obj)

def send_command(req, host, port, filename=None, save=False):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            client_socket.connect((host, port))
        except ConnectionRefusedError as e:
            if e.errno == 111:
                logging.error("No vern server detected")
                sys.exit(1)
            else:
                raise
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")

        logging.debug(f"Sending {req}")
        client_socket.sendall(req.encode())

        l = receive_length(client_socket)
        logging.debug(f'Receive length of response {l}')
        data = receive_exact_bytes(client_socket, l)
        return data


def load_config(config_path, overrides=None):
    """Load YAML config and allow overrides via a dictionary."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Expand user/home directory
    for key, value in config.get("settings", {}).items():
        if isinstance(value, str):
            config["settings"][key] = os.path.expandvars(os.path.expanduser(value))

    # Apply overrides (for testing)
    if overrides:
        for key, value in overrides.items():
            config["settings"][key] = value

    return config
