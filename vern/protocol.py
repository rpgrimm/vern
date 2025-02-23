#!/usr/bin/env python3

import json
import logging
import sys


#LOGIN = "login"
#GET_DATA = "get_data"
#SEND_MESSAGE = "send_message"

# Function to create a JSON request
def create_request(cid, sid, cmd, text=None, role=None, model='gpt-4o'):
    """
    Create a JSON request object.

    Args:
        cmd (str): The command type.
        text (str, optional): The text data associated with the command. Defaults to None.

    Returns:
        str: JSON string representing the request.
    """
    request_data = {
        "cid": cid,
        "sid": sid,
        "cmd": cmd,
        "text": text,
        "role": role,
        "model": model
    }
    return json.dumps(request_data)

# Function to parse a JSON request
def parse_request(json_str):
    """
    Parse a JSON request object.

    Args:
        json_str (str): JSON string representing the request.

    Returns:
        dict: Dictionary containing the parsed request data.
    """
    return json.loads(json_str)

def create_response(cid, sid, status, cmd, data=None):
    """
    Create a JSON response object.

    Args:
        status (str): The status of the response (e.g., "success" or "error").
        data (dict, optional): Additional data associated with the response. Defaults to None.

    Returns:
        str: JSON string representing the response.
    """
    return json.dumps({"cid": cid, "sid": sid, "status": status, "cmd": cmd, "data": data})

def parse_response(json_str):
    """
    Parse a JSON response object.

    Args:
        json_str (str): JSON string representing the response.

    Returns:
        dict: Dictionary containing the parsed response data.
    """

    """ Parse a JSON response and handle empty input gracefully """
    if not json_str or json_str.strip() == "":
        logging.error("Received an empty response from server")
        return {"status": "error", "cmd": "invalid", "data": "Empty response from server"}
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON received: {json_str}")
        return {"status": "error", "cmd": "invalid", "data": "Malformed response from server"}

def recv_json(sock):
    """
    Receive JSON data from the socket.

    Args:
        sock (socket.socket): The socket object.

    Returns:
        dict: The parsed JSON data.
    """
    json_data = b""  # Initialize an empty bytes object to store received data
    while True:
        chunk = sock.recv(1024)  # Receive data in chunks
        if not chunk:  # If no more data is received
            break  # Break the loop
        json_data += chunk  # Append the received chunk to the bytes object
        try:
            # Attempt to decode the bytes object as UTF-8 and parse it as JSON
            return json.loads(json_data.decode("utf-8"))
        except json.JSONDecodeError:
            continue  # If decoding/parsing fails, continue receiving data

