import os
import time
import json
import pytest
import subprocess
import socket

from protocol import create_request, parse_response
from utils import send_command

import server


@pytest.fixture(scope="function")
def start_vern_server(tmp_path):
    """Starts the vern server in daemon mode and ensures cleanup after tests."""
    config = {
        "settings": {"dpath": str(tmp_path)},
        "network": {"host": "localhost", "port": 54320},
    }

    #server.main(argv=['-i'], config=config)  # Pass config as a dict
    server.main(argv="", config=config)  # Pass config as a dict
    
    time.sleep(1)

    yield config  # Yield config instead of server

def test_server_running(start_vern_server):
    """Check that the server is running and accepting connections."""
    server_host = start_vern_server["network"]["host"]
    server_port = start_vern_server["network"]["port"]

    # Create a test request
    request = create_request("test", "init", "hello, server!")

    # Send the request to the server
    data = send_command(request, server_host, server_port)
    response = parse_response(data)

    # Check that the response status is success
    assert response["status"] == "success"
