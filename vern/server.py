#!/usr/bin/env python3

import argparse
import atexit
import logging
import os
import pickle
import random
import re
import select
import socket
import sys
import shutil
import tempfile
import threading
import time

from protocol import create_response, recv_json
import config
from session import ClientContext
from ai_handler import AIHandler
from utils import find_available_port, write_server_info_to_file


class CommandListener:
    #def __init__(self, model="gpt-4o"):
    def __init__(self, model="gpt-4o-mini"):
        self.host = 'localhost'
        self.port = find_available_port()
        self.running = False
        self.model = model
        self.ai_handler = AIHandler()

        logging.info(f"Using model {model}")

        self.ctxts = {}
        self.ctxts_max = 1000
        self.supported_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"]
        os.makedirs(config.path, exist_ok=True)
        os.makedirs(config.dpath, exist_ok=True)

        self.temp_dir = tempfile.mkdtemp(prefix="vern-", dir="/var/tmp/")
        logging.info(f"Using temporary directory: {self.temp_dir}")

        atexit.register(self.cleanup)

    def cleanup(self):
        """Remove the temporary directory on server shutdown."""
        try:
            shutil.rmtree(self.temp_dir)
            logging.info(f"Removed temporary directory: {self.temp_dir}")
        except Exception as e:
            logging.error(f"Failed to remove temp dir {self.temp_dir}: {e}")

    def ctxt_create(self, cid, sid, role='Act as a helpful tech-savvy assistant'):
        """ Create a new client session """
        logging.debug(f'Creating context {cid} {sid}')

        while cid == -1:
            cid = random.randint(1, self.ctxts_max)
            if cid not in self.ctxts:
                break

        if sid == -1:
            sid = self.find_next_sid()

        ctxt = ClientContext(cid, sid, role=role)
        self.ctxts[(cid, sid)] = ctxt
        return ctxt

    def find_next_sid(self):
        """ Find the next available session ID based on existing session files. """
        session_files = [f for f in os.listdir(config.dpath) if re.match(r'^session-\d+$', f)]
        if session_files:
            sids = [int(re.search(r'\d+', f).group()) for f in session_files]
            return max(sids) + 1
        return 1

    def send_ack(self, ctxt, client_socket):
        """Send an ACK (Acknowledgment) response to the client."""
        ack = create_response(ctxt.cid, ctxt.sid, 'success', 'ack', 'operation successful')
        self.send_response(client_socket, ack)

    def send_nack(self, ctxt, client_socket, reason):
        """Send a NACK (Negative Acknowledgment) response to the client with an error message."""
        nack = create_response(ctxt.cid if ctxt else -1, ctxt.sid if ctxt else -1, 'error', 'nack', reason)
        self.send_response(client_socket, nack)

    def send_response(self, client_socket, response):
        """Send a JSON response to the client."""
        response_bytes = response.encode()
        client_socket.sendall(len(response_bytes).to_bytes(4, byteorder='big'))
        client_socket.sendall(response_bytes)

    def send_obj(self, client_socket, obj):
        """Send a serialized object to the client."""
        obj_bytes = pickle.dumps(obj)
        client_socket.sendall(len(obj_bytes).to_bytes(4, byteorder='big'))
        client_socket.sendall(obj_bytes)

    def handle_client(self, client_socket):
        """Handles client requests and executes the appropriate commands."""
        with client_socket:
            try:
                json_data = recv_json(client_socket)
                cid, sid, cmd, text, role = json_data['cid'], json_data['sid'], json_data['cmd'], json_data['text'], json_data['role']

                logging.debug(f"Received: {json_data}")
                #ctxt = self.ctxts.get((cid, sid)) or self.ctxt_create(json_data)

                if cmd == 'init':
                    """Initialize the session and save it"""
                    ctxt = self.ctxt_create(cid, sid)
                    ctxt.write_session_file()
                    self.send_response(client_socket, create_response(ctxt.cid, ctxt.sid, 'success', 'none', 'none'))
                    logging.info(f'Client cid:{ctxt.cid} sid:{ctxt.sid} initialized')

                elif cmd == 'query':
                    """Handle AI queries and responses"""
                    logging.debug(f"Processing query: {text}")

                    ctxt = self.ctxts.get((cid, sid))
                    ctxt.load_session_messages()

                    ctxt.new_message('user', text)
                    d_airesponse = self.ai_handler.get_airesponse(ctxt)  # Get AI response

                    if d_airesponse['status'] == 'error':
                        logging.error(f"AI Error: {d_airesponse['message']}")
                        self.send_response(client_socket, create_response(ctxt.cid, ctxt.sid, 'error', d_airesponse['code'], d_airesponse['message']))
                        return

                    ai_text_response = d_airesponse['data'].choices[0].message.content

                    # Save response in session history
                    ctxt.new_message("assistant", ai_text_response)
                    ctxt.write_session_file()

                    self.send_response(client_socket, create_response(ctxt.cid, ctxt.sid, 'success', 'airesponsetofollow', 'not_applicable'))
                    self.send_obj(client_socket, d_airesponse['data'])

                elif cmd == 'new-s':
                    """Handle new session creation"""
                    session_file = os.path.join(config.dpath, f'session-{text}')
                    if os.path.exists(session_file):
                        logging.debug(f'Session {text} already exists, sending nack')
                        ctxt = self.ctxt_create(-1, -1)
                        self.send_nack(ctxt, client_socket, f'session-{text} exists')
                        return

                    ctxt = self.ctxt_create(-1, text, role=role)
                    logging.info(f"Starting new session @ {session_file}")
                    ctxt.write_session_file()
                    self.send_ack(ctxt, client_socket)

                elif cmd == 'use-s':
                    """Handle using an existing session"""
                    session_file = os.path.join(config.dpath, f'session-{text}')

                    if not os.path.exists(session_file):
                        logging.debug(f'Session {text} DOES NOT exist, sending nack')
                        ctxt = self.ctxt_create(-1, -1)
                        self.send_nack(ctxt, client_socket, f'session-{text} DOES NOT exist')
                        return

                    logging.debug(f"Using existing session {session_file}")
                    #--use-s has text as sid to use
                    logging.info(f'About to get cid {cid} sid {text}')
                    ctxt = self.ctxts.get((cid, text)) or self.ctxt_create(-1, text)
                    ctxt.load_session_messages()
                    self.send_ack(ctxt, client_socket)

                elif cmd == 'rm-s':
                    """Moves a session to the temp dir's 'trash' instead of deleting it."""

                    session_path = os.path.join(config.dpath, f"session-{text}")
                    trash_dir = os.path.join(self.temp_dir, "trash")
                    os.makedirs(trash_dir, exist_ok=True)  # ✅ Ensure trash directory exists
                    ctxt = self.ctxt_create(-1, -1)

                    if not os.path.exists(session_path):
                        self.send_nack(ctxt, client_socket, f"Session {text} does not exist.")
                        return

                    # ✅ Generate unique trash filename (session-name, session-name-1, session-name-2, etc.)
                    base_name = f"session-{text}"
                    trash_path = os.path.join(trash_dir, base_name)
                    counter = 0

                    while os.path.exists(trash_path):
                        counter += 1
                        trash_path = os.path.join(trash_dir, f"{base_name}-{counter}")

                    # ✅ Move session to trash
                    shutil.move(session_path, trash_path)
                    logging.info(f"Moved session {text} to trash as {os.path.basename(trash_path)}")
                    self.send_ack(ctxt, client_socket)

                elif cmd == 'list-s':
                    """Lists all session names in dpath, sorting numbers first, then alphabetically."""
                    try:
                        session_files = [f for f in os.listdir(config.dpath) if f.startswith("session-")]
                        session_names = [re.sub(r"^session-", "", f) for f in session_files]  # Extract names

                        # ✅ Sort: Numbers first, then alphabetically
                        def sort_key(name):
                            return (not name.isdigit(), name if name.isdigit() else name.lower())  # Numbers first, then case-insensitive names

                        session_names.sort(key=sort_key)

                        response_data = "\n".join(session_names) if session_names else "No sessions found."
                        self.send_response(client_socket, create_response(-1, -1, "success", "list-s", response_data))

                    except Exception as e:
                        self.send_response(client_socket, create_response(-1, -1, "error", "list-s-failed", str(e)))

                elif cmd == 'list-m':

                    try:
                        models = self.ai_handler.list_models()
                        self.debug(f'models: {models}')


                    except Exception as e:
                        self.send_response(client_socket, create_response(-1, -1, "error", "list-m-failed", str(e)))

                elif cmd == 'new-r':
                    """Handle setting a new role"""

                    ctxt = self.ctxts.get((cid, sid))
                    if not ctxt:
                        logging.debug(f'Session {sid} not found, sending nack')
                        self.send_nack(ctxt, client_socket, f'Session {sid} not found')
                        return

                    logging.debug(f"Setting new role for session {sid}: {text}")

                    ctxt.new_message('system', text)
                    ctxt.write_session_file()
                    self.send_ack(ctxt, client_socket)

                else:
                    logging.error(f"Invalid command: {cmd}")
                    self.send_nack(ctxt, client_socket, "Invalid command")

            except Exception as e:
                logging.error(f"Unhandled error: {e}")
                self.send_response(client_socket, create_response(-1, -1, 'error', 'server_error', str(e)))
                import traceback
                print(traceback.format_exc())


    def start(self):
        self.running = True
        threading.Thread(target=self.server_thread, daemon=True).start()
        write_server_info_to_file(self.host, self.port)

    def server_thread(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen()

            logging.info(f"Vern server listening on {self.host}:{self.port}")
            while self.running:
                readable, _, _ = select.select([server_socket], [], [], 0.1)
                for sock in readable:
                    if sock == server_socket:
                        client_socket, _ = server_socket.accept()
                        threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

    def stop(self):
        self.running = False

    def dump(self):
        """ Print all active client contexts. """
        logging.info("Dumping client contexts:")
        if not self.ctxts:
            logging.info("No active client contexts.")
            return

        for (cid, sid), ctxt in self.ctxts.items():
            print("***********************************************************************************************")
            print(f"Client ID: {cid} | Session ID: {sid} | Model: {ctxt.model}")
            print("Messages:")
            for message in ctxt.messages:
                print(f"  - {message}")
            print("***********************************************************************************************")


def main():
    parser = argparse.ArgumentParser(description='Listen for commands from client')
    parser.add_argument('-d', '--debug', action='store_true', help='Print debug messages')
    parser.add_argument('-i', '--interactive', action='store_true', help='Interactive mode')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format='%(asctime)s - %(levelname)s - L%(lineno)d - %(message)s')

    # Suppress excessive HTTP logs
    logging.getLogger("http.client").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    command_listener = CommandListener()
    command_listener.start()

    try:
        while args.interactive:
            command = input("Enter 'q' to quit: ")
            if command.lower() == 'q':
                command_listener.stop()
                break
            elif command.lower() == 'd':
                logging.debug("Dumping client contexts")
                command_listener.dump()
    except KeyboardInterrupt:
        command_listener.stop()


if __name__ == "__main__":
    main()

