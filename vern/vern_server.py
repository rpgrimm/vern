#!/usr/bin/env python3

import argparse
import atexit
import json
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
import yaml

from daemonize import Daemonize
from protocol import create_response, recv_json
from session_context import SessionContext
from ai_handler import AIHandler
from utils import find_available_port, write_server_info_to_file, load_config


class CommandListener():

    def __init__(self, config):

        self.config = config
        logging.debug(self.config)

        self.running = False
        self.ai_handler = AIHandler(config)

        logging.info(f"Using model {config['settings']['model']}")
        self.model = config['settings']['model']

        self.session_contexts = {}
        self.sessions = {}
        self.supported_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"]
        os.makedirs(self.config['settings']['dpath'], exist_ok=True)

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

    def send_ack(self, sid, client_socket):
        """Send an ACK (Acknowledgment) response to the client."""
        ack = create_response(sid, 'success', 'ack', 'operation successful')
        self.send_response(client_socket, ack)

    def send_nack(self, sid, client_socket, reason='None given'):
        """Send a NACK (Negative Acknowledgment) response to the client with an error message."""
        nack = create_response(sid, 'error', 'nack', reason)
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

    def is_server_running(self):
        return self.server_thread.is_alive()

    def is_session_active(self, sid):
        return sid in self.session_contexts

    def does_session_dir_exist(self, sid):
        return SessionContext.session_exists(self.config['settings']['dpath'], sid)

    def do_ai_query(self, client_socket, session_context, data):
        session_context.add_user_content(data)
        d_airesponse = self.ai_handler.get_airesponse(session_context)  # Get AI response

        if d_airesponse['status'] == 'error':
            logging.error(f"AI Error: {d_airesponse['message']}")
            self.send_response(client_socket, create_response(session_context.sid, 'error', d_airesponse['code'], d_airesponse['message']))
            return

        ai_text_response = d_airesponse['data'].choices[0].message.content

        # Save response in session history
        session_context.add_assistant_content(ai_text_response)

        self.send_response(client_socket, create_response(session_context.sid, 'success', 'airesponsetofollow', 'not_applicable'))
        self.send_obj(client_socket, d_airesponse['data'])

    def do_ai_query_oneshot(self, client_socket, session_context, data):
        d_airesponse = self.ai_handler.get_airesponse_oneshot(session_context, data)  # Get AI response

        if d_airesponse['status'] == 'error':
            logging.error(f"AI Error: {d_airesponse['message']}")
            self.send_response(client_socket, create_response(session_context.sid, 'error', d_airesponse['code'], d_airesponse['message']))
            return

        ai_text_response = d_airesponse['data'].choices[0].message.content

        # Save response in session history
        session_context.add_oneshot_content(ai_text_response)

        self.send_response(client_socket, create_response(session_context.sid, 'success', 'airesponsetofollow', 'not_applicable'))
        self.send_obj(client_socket, d_airesponse['data'])


    def find_session_for_client(self, client_socket, sid):
        if self.is_session_active(sid):
            session_context = self.session_contexts[sid]

        elif self.does_session_dir_exist(sid):
            session_context = SessionContext(sid)
            self.session_contexts[sid] = session_context

        else:
            logging.error(f"Session session-{sid} does not exist")
            self.send_nack(sid, client_socket, f"Session session-{sid} does not exist")
            return None
        return session_context

    def handle_client(self, client_socket):
        """Handles client requests and executes the appropriate commands."""
        with client_socket:
            try:
                json_data = recv_json(client_socket)

                logging.debug(f"Received: {json_data}")

                if json_data['cmd'] == 'init-ppid-session':
                    """Initialize the session and save it"""

                    # check if this session has been initialized
                    if json_data['sid'] in self.session_contexts:
                        logging.info(f'Session {json_data['sid']} exists')
                        session_context = self.session_contexts[json_data['sid']]
                        self.send_response(client_socket, create_response(json_data['sid'], 'success', 'none', 'none'))
                    else:
                        session_context = SessionContext(json_data['sid'], self.config, ppid=True)
                        self.session_contexts[json_data['sid']] = session_context
                        self.send_response(client_socket, create_response(json_data['sid'], 'success', 'none', 'none'))
                        logging.info(f'Session {json_data['sid']} initialized')

                elif json_data['cmd'] == 'exit':
                    self.send_response(client_socket, create_response(json_data['sid'], 'success', 'none', 'none'))
                    logging.info(f'Exiting')
                    self.running = False

                elif json_data['cmd'] == 'query':
                    """Handle AI queries and responses"""
                    logging.debug(f"Processing query: {json_data['data']}")

                    session_context = SessionContext(json_data['sid'])
                    self.session_contexts[json_data['sid']] = session_context

                    self.do_ai_query(client_socket, session_context, json_data['data'])

                elif json_data['cmd'] == 'new-user-s':
                    """Handle new session creation"""

                    logging.debug(f"New session session-{json_data['sid']} requested")

                    if self.is_session_active(json_data['sid']) or self.does_session_dir_exist(json_data['sid']):
                        logging.error(f"Session session-{json_data['sid']} already exists")
                        self.send_nack(json_data['sid'], client_socket, f"Session session-{json_data['sid']} already exists")
                    else:
                        session_context = SessionContext(json_data['sid'], system_content=json_data['data'])
                        self.session_contexts[json_data['sid']] = session_context
                        logging.info(f"Startet new session @ {session_context.session_dir}")

                        self.send_ack(json_data['sid'], client_socket)

                elif json_data['cmd'] == 'system':

                    logging.debug(f"New system for session-{json_data['sid']} requested")

                    if (session_context := self.find_session_for_client(client_socket, json_data['sid'])) is None:
                        return

                    session_context.set_system_content(json_data['data'])


                elif json_data['cmd'] == 'use-s-query':
                    """Handle using an existing session query"""

                    if (session_context := self.find_session_for_client(client_socket, json_data['sid'])) is None:
                        return

                    self.do_ai_query(client_socket, session_context, json_data['data'])

                elif json_data['cmd'] == 'use-s-system':
                    """Handle using an existing session system"""

                    if (session_context := self.find_session_for_client(client_socket, json_data['sid'])) is None:
                        return

                    session_context.set_system_content(json_data['data'])
                    self.send_ack(json_data['sid'], client_socket)

                elif json_data['cmd'] == 'use-s-oneshot':
                    """Handle using an existing session system"""

                    if (session_context := self.find_session_for_client(client_socket, json_data['sid'])) is None:
                        return

                    user_content = [{'role' : 'user', 'content' : json_data['data']}]
                    self.do_ai_query_oneshot(client_socket, session_context, user_content)
                    self.send_ack(json_data['sid'], client_socket)

                elif json_data['cmd'] == 'use-sys':

                    if (session_context := self.find_session_for_client(client_socket, json_data['sid'])) is None:
                        return

                    session_context.set_system_content(json_data['system'])
                    self.do_ai_query(client_socket, session_context, json_data['data'])
                    self.send_ack(json_data['sid'], client_socket)

                elif json_data['cmd'] == 'rm-s':
                    """Moves a session to the temp dir's 'trash' instead of deleting it."""

                    session_context = self.find_session_for_client(client_socket, json_data['sid'])
                    if session_context is None:
                        return
                    session_context.remove_session(self.temp_dir, self.config['settings']['dpath'], json_data['sid'])
                    if json_data['sid'] in self.session_contexts:
                        del self.session_contexts[json_data['sid']]
                    self.send_ack(json_data['sid'], client_socket)

                elif json_data['cmd'] == 'list-s':
                    """Lists all valid session directories in dpath, sorting numbers first, then alphabetically,
                    and includes a truncated version of the system.json content (first 70 characters).
                    """
                    try:
                        session_base = self.config['settings']['dpath']
                        session_data = []

                        for f in os.listdir(session_base):
                            session_path = os.path.join(session_base, f)
                            if os.path.isdir(session_path) and f.startswith("session-"):
                                system_json = os.path.join(session_path, "system.json")
                                conversation_json = os.path.join(session_path, "conversation.json")

                                if os.path.isfile(system_json) and os.path.isfile(conversation_json):
                                    sid = re.sub(r"^session-", "", f)  # Extract SID

                                    # Read system.json content
                                    try:
                                        with open(system_json, 'r', encoding='utf-8') as sys_file:
                                            system_content = sys_file.read()
                                            system_content = json.loads(system_content).get("content", "").strip()
                                            if len(system_content) > 70:
                                                system_content = system_content[:70] + "..."
                                    except Exception as read_error:
                                        logging.error(f"Error reading system.json for session-{sid}: {read_error}")
                                        system_content = "Error reading system.json."

                                    session_data.append((sid, system_content))

                        # ✅ Sort: Numbers first, then alphabetically
                        def sort_key(item):
                            name = item[0]
                            return (not name.isdigit(), name if name.isdigit() else name.lower())  # Numbers first, then case-insensitive names

                        session_data.sort(key=sort_key)

                        if session_data:
                            response_data = "\n".join(
                                [f"session-{sid} {system_content}" for sid, system_content in session_data]
                            )
                        else:
                            response_data = "No valid sessions found."

                        self.send_response(client_socket, create_response(-1, "success", "list-s", response_data))

                    except Exception as e:
                        logging.error(f"Error listing session directories: {e}")
                        self.send_response(client_socket, create_response(-1, "error", "list-s", f"Error: {e}"))


                elif json_data['cmd'] == 'list-m':

                    try:
                        models = self.ai_handler.list_models()
                        model_ids = [model.id for model in models.data]
                        response_data = " ".join(model_ids)
                        self.send_response(client_socket, create_response(-1, "success", "list-m", response_data))

                        logging.debug(model_ids)


                    except Exception as e:
                        self.send_response(client_socket, create_response(-1, "error", "list-m-failed", str(e)))

                elif json_data['cmd'] == 'use-model':
                    if (session_context := self.find_session_for_client(client_socket, json_data['sid'])) is None:
                        return

                    session_context.set_model(json_data['data'])
                    self.send_ack(json_data['sid'], client_socket)

                elif json_data['cmd'] == 'reset':

                    if (session_context := self.find_session_for_client(client_socket, json_data['sid'])) is None:
                        return

                    session_context.reset(json_data['sid'])
                    self.send_ack(json_data['sid'], client_socket)

                else:
                    logging.error(f"Invalid command: {json_data['cmd']}")
                    self.send_nack(json_data['sid'], client_socket, "Invalid command")

            except Exception as e:
                logging.error(f"Unhandled error: {e}")
                self.send_response(client_socket, create_response(-1, 'error', 'server_error', str(e)))
                import traceback
                print(traceback.format_exc())


    def start(self):
        self.running = True
        self.server_thread = threading.Thread(target=self.server_thread_func, daemon=False)
        self.server_thread.start()
        write_server_info_to_file(self.config['network']['host'], self.config['network']['port'])

    def server_thread_func(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.config['network']['host'], self.config['network']['port']))
            server_socket.listen()

            logging.info(f"Vern server listening on {self.config['network']['host']}:{self.config['network']['port']}")
            while self.running:
                readable, _, _ = select.select([server_socket], [], [], 0.1)
                for sock in readable:
                    if sock == server_socket:
                        client_socket, _ = server_socket.accept()
                        threading.Thread(target=self.handle_client, args=(client_socket,), daemon=False).start()

    def stop(self):
        self.running = False

    def dump(self):
        """ Print all active session contexts. """
        if not self.session_contexts:
            logging.info("No active session contexts.")
            return

        for sid, ctxt in self.session_contexts.items():
            print("***********************************************************************************************")
            print(f"Session ID: {sid} | Model: {ctxt.model}")
            print(f"System Content: {ctxt.system_content}")
            print("User and Assistant Content:")
            if not ctxt.user_and_assistant_content:
                print(" [ No messages ]")
            else:
                for message in ctxt.user_and_assistant_content:
                    print(f"  - {message}")
            print("***********************************************************************************************")

def show_all_threads():
    # List all running threads
    threads = threading.enumerate()

    print("Active Threads:")
    for thread in threads:
        print(f"Thread Name: {thread.name}, ID: {thread.ident}, Daemon: {thread.daemon}")

def main_daemon():
    command_listener = CommandListener(config)
    command_listener.start()
    while command_listener.running:
        time.sleep(.1)

def main(argv = sys.argv[1:], config=None):
    parser = argparse.ArgumentParser(description='Listen for commands from client')
    parser.add_argument('-d', '--debug', action='store_true', help='Print debug messages')
    parser.add_argument('-i', '--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('-c', '--config', type=str, help='Provide path to config.yaml')
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format='%(asctime)s - %(levelname)s - L%(lineno)d - %(message)s')
    # Suppress excessive HTTP logs
    logging.getLogger("http.client").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    script_path = os.path.dirname(os.path.abspath(__file__))

    if config is None:
        config_path = args.config or os.path.join(script_path, "config.yaml")
        config = load_config(config_path)

    if not args.interactive:
        pid = os.path.join(config['settings']['dpath'], "vern.pid")
        daemon = Daemonize(app="vern_server", pid=pid, action=main_daemon)
        rc = daemon.start()
        sys.exit(0)

    command_listener = CommandListener(config)
    command_listener.start()

    def non_blocking_input(prompt, timeout=0.1):
        """Check for input with a timeout."""
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            return sys.stdin.readline().strip()  # Read input if available
        return None  # No input

    # Print the prompt once before entering the loop
    sys.stdout.write("Enter 'q' to quit: ")
    sys.stdout.flush()

    try:
        while command_listener.running:
            command = non_blocking_input("Enter 'q' to quit: ", timeout=0.1)
            if command:
                if command.lower() == 'q':
                    command_listener.stop()
                    break
                elif command.lower() == 'd':
                    command_listener.dump()
                elif command.lower() == 't':
                    show_all_threads()

                # Reprint the prompt only after processing a command
                sys.stdout.write("Enter 'q' to quit: ")
                sys.stdout.flush()
            else:
                # No input received, perform other tasks or continue polling
                pass

    except KeyboardInterrupt:
        command_listener.stop()
        print("\nExiting...")


if __name__ == "__main__":
    main()
