#!/usr/bin/env python3

import logging
import sys
import socket
import argparse
import readline
import os
import shutil
import time
import pickle

from protocol import create_request, parse_response
import config
from utils import receive_exact_bytes, receive_length, read_server_info, open_vim
from history import load_history, save_history

from colorama import init, Fore
from rich.console import Console
from rich.markdown import Markdown

class Client:
    def __init__(self, sid=None, model="gpt-4o-mini", no_markdown=False, save_responses=False):
        self.cid = -1
        self.sid = sid if sid else -1
        self.no_markdown = no_markdown
        self.save_responses = save_responses
        self.response_count = 0  # Counter for responses

        self.host, self.port = read_server_info(f"{config.path}/server_info.txt")
        if not self.host or not self.port:
            logging.error("Couldn't read server_info.txt")
            sys.exit(1)

    def load_history(self):
        load_history(self.history_file)

    def server_init(self):
        """Initialize server session and retrieve a client ID (cid)."""
        request = create_request(self.cid, self.sid, "init", "allow me to introduce myself")
        myresponse = self.send_command(request)
        if myresponse["status"] == "success":
            self.cid = myresponse["cid"]
            self.sid = myresponse["sid"]
            logging.debug(f"Client initialized with cid={self.cid}, sid={self.sid}")
        else:
            logging.error("Failed to initialize AI session")

        # Set up history file once we get our sid
        self.history_file = os.path.join(config.dpath, f"history-{self.sid}.txt")

    def do_message(self, msg):
        req = create_request(self.cid, self.sid, 'query', msg)
        json_data = self.send_command(req)
        logging.debug(f"Got response {json_data}")

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

            l = receive_length(client_socket)
            logging.debug(f'Receive length of response {l}')
            data = receive_exact_bytes(client_socket, l)
            logging.debug(data)
            json_data = parse_response(data)

            self.cid = json_data['cid']
            status = json_data['status']
            data = json_data['data']
            cmd = json_data['cmd']

            if json_data['status'] == 'error':
                logging.error(f'cmd: {cmd} data: {data}')

            if json_data['cmd'] == 'airesponsetofollow':
                logging.debug("Getting airesponse")
                l = receive_length(client_socket)
                response = receive_exact_bytes(client_socket, l)
                response = pickle.loads(response)
                lines = " ".join(choice.message.content for choice in response.choices)

                if self.no_markdown:
                    print(lines)
                else:
                    self.response_count += 1
                    #color = "gray" if self.response_count % 2 == 0 else "white"
                    color="bright_white"
                    md = Markdown(lines)
                    console.print(md, style=color)

                if self.save_responses:
                    response_filename = f"{config.dpath}/responses-{self.cid}-{self.sid}"
                    with open(response_filename, 'a') as f:
                        f.write(lines)

                if save:
                    with open(filename, 'w') as f:
                        f.write(lines)

            return json_data

    def new_s(self, sid, role=None):
        self.sid = sid
        req = create_request(self.cid, self.sid, 'new-s', sid, role)
        json_data = self.send_command(req)
        if json_data['status'] == 'nack':
            print(Fore.RED + f"FAIL: {json_data['cmd']}")
        #set up history file once we confirm our sid
        self.history_file = os.path.join(config.dpath, f"history-{self.sid}.txt")

    def use_s(self, sid):
        self.sid = sid
        req = create_request(self.cid, self.sid, 'use-s', sid)
        json_data = self.send_command(req)

        if json_data['status'] == 'error':
            sys.exit(1)
        #set up history file once we confirm our sid
        self.history_file = os.path.join(config.dpath, f"history-{self.sid}.txt")

    def rm_s(self, sid):
        self.sid = sid
        req = create_request(self.cid, self.sid, 'rm-s', sid)
        json_data = self.send_command(req)

        if json_data['status'] == 'error':
            sys.exit(1)

    def list_s(self):
        req = create_request(self.cid, self.sid, 'list-s')
        json_data = self.send_command(req)

        if json_data['status'] == 'error':
            sys.exit(1)

        print(json_data['data'])

    def list_models(self):
        req = create_request(self.cid, self.sid, 'list-m')
        json_data = self.send_command(req)

        if json_data['status'] == 'error':
            sys.exit(1)

        print(json_data['data'])

    def show_help(self):
        """Displays the available interactive commands."""
        print("\n🔹 Interactive Mode Commands 🔹")
        print("  d  - Dump client info (cid, sid)")
        print("  q  - Quit and save history")
        print("  lr - Show last response")
        print("  h  - Show this help menu")
        print("  l <session_id> - Load session")
        print("  s <session_name> - Save session")
        print("  e  - Edit message in Vim")
        print("  <message> - Send message to the AI\n")

    def go_interactive(self):
        """Interactive client mode for sending messages to the server."""
        try:
            while True:
                input_text = input("vern> ").strip()

                if input_text == "d":
                    logging.info(f"Dumping info: cid={self.cid}, sid={self.sid}")

                elif input_text == "q":
                    readline.remove_history_item(readline.get_current_history_length() - 1)
                    save_history(self.history_file)
                    print("Goodbye!")
                    sys.exit(0)

                elif input_text == "lr":
                    print("🔍 Fetching last response...")
                    self.do_message("show me the last response")

                elif input_text in ["h", "?"]:
                    self.show_help()  # ✅ Call the help menu function

                elif input_text.startswith("l "):
                    self.load_s(input_text[2:])

                elif input_text.startswith("s "):
                    self.save_session(input_text[2:])

                elif input_text == "e":
                    text = open_vim()
                    self.do_message(text)

                elif input_text == "":
                    pass  # Ignore empty input

                else:
                    self.do_message(input_text)

        except (EOFError, KeyboardInterrupt):
            save_history(self.history_file)
            print("\nExiting and saving history. Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    from cli import parse_args
    args = parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    console = Console()
    init(autoreset=True)

    client = Client(no_markdown=args.no_markdown, save_responses=args.save_responses)

    if args.rm_s:
        client.rm_s(args.rm_s[0])
        sys.exit(0)

    if args.list_s:
        client.list_s()
        sys.exit(0)

    if args.new_s:
        sid = args.new_s[0]
        role = " ".join(args.new_s[1:]) if len(args.new_s) > 1 else None
        client.new_s(sid, role)
        sys.exit(0)

    if args.list_m:
        client.list_models()

    if not args.stdin:
        if args.use_s:
            sid = args.use_s[0]
            client.use_s(sid)
            if len(args.args) > 0:
                client.do_message(" ".join(args.args))
        elif len(args.args) > 0:
            client.server_init()
            client.do_message(" ".join(args.args))
            sys.exit(0)
    else:
        if args.use_s:
            sid = args.use_s[0]
            client.use_s(sid)
        else:
            client.server_init()

        input_text = sys.stdin.read().strip()  # ✅ Strip trailing newlines/spaces
        if not input_text:
            logging.warning("⚠️ No input received from stdin.")
        else:
            logging.debug(f"📥 Received input from stdin: {input_text[:100]}...")  # ✅ Limit log size
            if args.message:
                client.do_message(f'I\'m about to send text your way and I want you to {args.message}')
            client.do_message(input_text)

    if not args.use_s:
        client.server_init()

    if args.interactive:
        client.load_history()
        client.go_interactive()
