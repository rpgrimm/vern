import config
import os
import subprocess
import socket
import time

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

def read_server_info(filename):
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            if len(lines) == 2:
                return lines[0].strip(), int(lines[1].strip())
    except (FileNotFoundError, ValueError):
        return None, None

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
    with open(f"{config.path}/server_info.txt", 'w') as f:
        f.write(f"{host}\n{port}")

def send_response(client_socket, response):
    client_socket.sendall(len(response).to_bytes(4, 'big'))
    client_socket.sendall(response.encode())

def send_obj(client_socket, obj):
    client_socket.sendall(len(obj).to_bytes(4, 'big'))
    client_socket.sendall(obj)

