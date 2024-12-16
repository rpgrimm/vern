#!/usr/bin/env python3

import logging
import markdown
import pickle
import subprocess
import sys
import socket
import time
import argparse
import readline
import os
import shutil

from protocol import create_request, parse_response
import config

from colorama import init, Fore, Style
from rich.console import Console
from rich.markdown import Markdown

class Client:
    def __init__(self, sid=None, model="gpt-4o-turbo", no_markdown=False, save_responses=False):
        self.cid = -1
        self.sid = sid if sid else -1
        self.no_markdown = no_markdown
        self.save_responses = save_responses
        self.response_count = 0  # Counter for responses

        host, port = self.read_server_info(f"{config.path}/server_info.txt")
        if not host or not port:
            logging.error("Couldn't read server_info.txt")
            sys.exit(1)

        self.host = host
        self.port = port
        # Set the history file dynamically based on session ID in dpath
        self.history_file = os.path.join(config.dpath, f"client_history_{self.sid}.txt")

        # Load the history file for the session
        self.load_history(self.history_file)

    def aiinit(self):
        request = create_request(self.cid, self.sid, 'init', 'allow me to introduce myself')
        myresponse = self.send_command(request)
        if myresponse['status'] == 'success':
            self.cid = myresponse['cid']
            self.sid = myresponse['sid']
            logging.debug(f"Got id {self.cid} session id {self.sid}")

    def load_history(self, history_file):
        if os.path.exists(history_file):
            with open(history_file, 'r') as file:
                history = file.read().splitlines()
            for line in history:
                readline.add_history(line)

    def save_history(self, history_file):
        history = [readline.get_history_item(i) for i in range(1, readline.get_current_history_length() + 1)]
        with open(history_file, 'w') as file:
            file.write('\n'.join(history))

    def receive_exact_bytes(self, connection, num_bytes):
        received_data = b""
        while len(received_data) < num_bytes:
            chunk = connection.recv(num_bytes - len(received_data))
            if not chunk:
                raise RuntimeError("Connection closed unexpectedly")
            received_data += chunk
        return received_data

    def receive_length(self, connection):
        length_bytes = connection.recv(4)
        return int.from_bytes(length_bytes, byteorder='big')

    def send_command(self, req, filename=None, save=False):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.connect((self.host, self.port))
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

            l = self.receive_length(client_socket)
            logging.debug(f'Receive length of response {l}')
            data = self.receive_exact_bytes(client_socket, l)
            logging.debug(data)
            json_data = parse_response(data)

            self.cid = json_data['cid']
            status = json_data['status']
            data = json_data['data']

            if json_data['cmd'] == 'airesponsetofollow':
                logging.debug("Getting airesponse")
                l = self.receive_length(client_socket)
                logging.debug(f'receive length of airesponse {l}')
                response = self.receive_exact_bytes(client_socket, l)
                response = pickle.loads(response)
                lines = "\n".join(choice.message.content for choice in response.choices)

                if self.no_markdown:
                    print(lines)
                else:
                    self.response_count += 1
                    color = "cyan" if self.response_count % 2 == 0 else "magenta"
                    md = Markdown(lines)
                    console.print(md, style=color)

                if self.save_responses:
                    with open(f'{config.dpath}/responses-{self.sid}', 'a') as f:
                        f.write(lines)

                if save:
                    with open(filename, 'w') as f:
                        f.write(lines)

            logging.debug(json_data)
            return json_data

    def open_vim(self):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"prompt-{timestamp}.txt"
        subprocess.run(['vim', filename])
        with open(filename, 'r') as file:
            return file.read()

    def read_server_info(self, filename):
        try:
            with open(filename, 'r') as file:
                lines = file.readlines()
                if len(lines) == 2:
                    host = lines[0].strip()
                    port = int(lines[1].strip())
                    return host, port
                else:
                    print("Invalid server info file format.")
        except FileNotFoundError:
            print("Server info file not found.")
        except ValueError:
            print("Invalid port number in server info file.")

    def new_s(self, sid, role=None):
        logging.debug(f"new-s {sid}")
        self.sid = sid
        req = create_request(self.cid, self.sid, 'new-s', sid, role)
        json_data = self.send_command(req)
        if json_data['status'] == 'nack':
            print(Fore.RED + f"FAIL: {json_data['cmd']}")
        logging.debug(f"Got response {json_data}")

    def new_r(self, role):
        req = create_request(self.cid, self.sid, 'new-r', role)
        json_data = self.send_command(req)
        logging.debug(f"Got response {json_data}")

    def use_s(self, sid):
        logging.debug(f"use_s {sid}")
        self.sid = sid
        req = create_request(self.cid, self.sid, 'use-s', sid)
        json_data = self.send_command(req)
        logging.debug(f"Got response {json_data}")

    def replay_s(self, sid):
        logging.debug(f"replay_s {sid}")
        self.sid = sid
        req = create_request(self.cid, self.sid, 'replay-s', sid)
        json_data = self.send_command(req)
        if json_data['status'] == 'nack':
            print(Fore.RED + f"FAIL: {json_data['cmd']}")
        logging.debug(f"Got response {json_data}")

    def load_s(self, sid):
        logging.debug(f"use_s {sid}")
        self.sid = sid
        req = create_request(self.cid, self.sid, 'load-s', sid)
        json_data = self.send_command(req)
        if json_data['status'] == 'nack':
            print(Fore.RED + f"FAIL: {json_data['cmd']}")
        logging.debug(f"Got response {json_data}")

    def do_message(self, msg):
        req = create_request(self.cid, self.sid, 'query', msg)
        json_data = self.send_command(req)
        logging.debug(f"Got response {json_data}")

    def use_model(self, model):
        req = create_request(self.cid, self.sid, 'model', model)
        json_data = self.send_command(req)
        print(json_data)

    def save_session(self, session_name):
        src_filename = os.path.join(config.dpath, f"session-{self.sid}")
        dest_filename = os.path.join(config.dpath, f"session-{session_name}")
        if os.path.exists(dest_filename):
            print(Fore.RED + f"File {dest_filename} already exists.")
        else:
            try:
                shutil.copy(src_filename, dest_filename)
                print(Fore.GREEN + f"Session saved as {dest_filename}")
            except FileNotFoundError:
                print(Fore.RED + f"Source file {src_filename} not found.")
            except Exception as e:
                print(Fore.RED + f"An error occurred while saving the session: {e}")

    def go_interactive(self):
        try:
            while True:
                input_text = input("vern> ")
                if input_text == 'd':
                    logging.info("Dumping info:")
                    logging.info(f"cid: {self.cid} sid: {self.sid}") 
                elif input_text == 'q':
                    # Remove 'q' from history
                    readline.remove_history_item(readline.get_current_history_length() - 1)
                    # Save the history before quitting
                    self.save_history(self.history_file)
                    print("Goodbye!")
                    sys.exit(0)
                elif input_text == 'lr':
                    # Command to show the last response
                    self.do_message("show me the last response")
                elif input_text in ['h', '?']:
                    print("d: dump info")
                    print("q: quit")
                    print("l <session_id>: load session")
                    print("s <session_name>: save session")
                    print("e: edit message in vim")
                    print("lr: show me the last response") 
                elif input_text.startswith('l '):
                    self.load_s(input_text[2:])
                elif input_text.startswith('s '):
                    session_name = input_text[2:]
                    self.save_session(session_name)
                elif input_text == 'e':
                    text = self.open_vim()
                    self.do_message(text)
                elif input_text == '':
                    pass
                else:
                    self.do_message(input_text)
        except (EOFError, KeyboardInterrupt):
            # Save the history when interrupted
            self.save_history(self.history_file)
            print("\nExiting and saving history. Goodbye!")
            sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Send text to server.')
    parser.add_argument('-f', '--file', help='Read text from file and send to server with command "n"')
    parser.add_argument('--stdin', action='store_true', help='Read input from stdin and send to server')
    parser.add_argument('-d', '--debug', action='store_true', help='Print debug messages')
    parser.add_argument('--new-s', type=str, nargs='+', help='Start a new session')
    parser.add_argument('--new-r', type=str, nargs='+', help='Start a new role')
    parser.add_argument('--use-s', type=str, nargs='+', help='Use an existing session')
    parser.add_argument('messages', type=str, nargs='*', help='Send messages and commands to send to the server')
    parser.add_argument('-m', '--model', type=str, nargs='*', help='Send messages and commands to send to the server')
    parser.add_argument('-i', '--interactive', action='store_true', help='Drop to interactive prompt')
    parser.add_argument('--no-markdown', action='store_true', help='Display response as raw markdown')
    parser.add_argument('-s', '--save-responses', action='store_true', help='Save all responses as text', default=config.save_responses)

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    console = Console()
    init(autoreset=True)

    if args.new_s:
        logging.debug(args.new_s)
        sid = args.new_s[0]
        client = Client(sid=sid, no_markdown=args.no_markdown, save_responses=args.save_responses)
        role = " ".join(args.new_s[1:]) if len(args.new_s) > 1 else None
        client.new_s(sid, role)
        sys.exit(0)

    if args.use_s:
        sid = args.use_s[0]
        client = Client(sid=sid, no_markdown=args.no_markdown, save_responses=args.save_responses)
        client.use_s(sid)

        if args.new_r:
            client.new_r(" ".join(args.new_r))
            sys.exit(0)
        elif args.file:
            try:
                with open(args.file, 'r') as file:
                    text = file.read()
                client.do_message(text)
            except FileNotFoundError:
                print("File not found.")
        elif not sys.stdin.isatty() or args.stdin:
            input_text = sys.stdin.read()
            logging.debug(f'Using {input_text}')
            client.do_message(input_text)
        elif len(args.use_s) > 1:
            logging.debug(f'Using session {args.use_s[0]} message {args.use_s[1:]}')
            client.do_message(" ".join(args.use_s[1:]))
            sys.exit(0)

        if args.model:
            client.use_model(args.model[0])

        if args.interactive:
            client.go_interactive()
    else:
        client = Client(no_markdown=args.no_markdown, save_responses=args.save_responses)
        client.aiinit()

        if args.interactive:
            client.go_interactive()
        elif len(args.messages) > 1:
            client.do_message(" ".join(args.messages))
        else:
            print("Nothing to do!")
