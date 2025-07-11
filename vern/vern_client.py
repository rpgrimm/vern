#!/usr/bin/env python3

import argparse
import json
import logging
import os
import pickle
import readline
import sys
import socket
import shutil
import time
import utils
import uuid

from protocol import create_request, parse_response
from utils import receive_exact_bytes, receive_length, read_server_info, open_vim, load_config
from history import load_history, save_history

from colorama import init, Fore, Style
from rich.console import Console
from rich.markdown import Markdown

class Client:
    def __init__(self, sid=None, config=None, no_markdown=False, save_responses=False):

        self.sid = sid if sid else f'ppid-{os.getppid()}'
        self.no_markdown = no_markdown
        self.save_responses = save_responses
        self.response_count = 0  # Counter for responses
        self.client_socket = None
        self.oneshot = False

        self.systems = self.load_systems()

        if config is None:
            script_path = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_path, "config.yaml")
            self.config = load_config(config_path)
        else:
            self.config = config

        self.host = self.config['network']['host']
        self.port = self.config['network']['port']

        init()

        #self.client_tmp_dir = self.create_client_tmp_dir()

    def handle_response(self, response_data):
        if response_data.get("status") == "error":
            print(Fore.RED + Style.BRIGHT)
            print("=== ERROR RESPONSE ===")
            print("Command:", json.dumps(response_data.get("cmd"), indent=2))
            print("Data:", json.dumps(response_data.get("data"), indent=2))
            print("======================")
            print(Style.RESET_ALL)
            return True
        return False

    def create_client_tmp_dir(self, base="/var/tmp/"):
        ppid = os.getppid()
        unique_id = uuid.uuid4().hex  # Generates a 32-char hex string
        dir_path = os.path.join(base, f"vern-client-{ppid}")
        os.makedirs(dir_path, exist_ok=True)
        with open(os.path.join(dir_path, 'sid'), "w") as f:
            f.write(unique_id)
        return dir_path

    def load_history(self):
        load_history(self.history_file)

    def server_exit(self):
        request = create_request(self.sid, "exit", "allow me to shut you down")
        myresponse = self.send_command(request)
        self.handle_response(myresponse)

    def server_init(self):
        """Initialize server session and retrieve a client ID (cid)."""
        request = create_request(self.sid, "init-ppid-session", "allow me to introduce myself")
        myresponse = self.send_command(request)
        if myresponse["status"] == "success":
            self.sid = myresponse["sid"]
            logging.debug(f"Client initialized with sid={self.sid}")
        else:
            logging.error("Failed to initialize AI session")

        # Set up history file once we get our sid
        self.history_file = os.path.join(self.config['settings']['dpath'], f"history-{self.sid}.txt")

    def do_user_content(self, msg):
        req = create_request(self.sid, 'query', msg, oneshot=self.oneshot)
        json_data = self.send_command(req)
        logging.debug(f"Got response {json_data}")
        self.handle_response(json_data)

    def send_command(self, req, filename=None, save=False):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.client_socket:
            try:
                self.client_socket.connect((self.host, self.port))
            except ConnectionRefusedError as e:
                if e.errno == 111:
                    logging.error("No vern server detected")
                    sys.exit(1)
                else:
                    raise
            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")

            logging.debug(f"Sending {req}")
            self.client_socket.sendall(req.encode())

            l = receive_length(self.client_socket)
            logging.debug(f'Receive length of response {l}')
            data = receive_exact_bytes(self.client_socket, l)
            logging.debug(data)

            json_data = parse_response(data)
            #if self.handle_response(json_data):
            #    sys.exit(0)
            status = json_data['status']
            data = json_data['data']
            cmd = json_data['cmd']

            if json_data['cmd'] == 'airesponsetofollow':
                logging.debug("Getting airesponse")
                l = receive_length(self.client_socket)
                response = receive_exact_bytes(self.client_socket, l)
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
                    response_filename = f"{self.config['settings']['dpath']}/responses-{self.sid}"
                    with open(response_filename, 'a') as f:
                        f.write(lines)

                if save:
                    with open(filename, 'w') as f:
                        f.write(lines)

            return json_data

    def load_systems(self):
        """Load predefined systems from systems.json."""
        script_dir = os.path.dirname(os.path.abspath(__file__))  # Get script's directory
        system_file = os.path.join(script_dir, "systems.json")  # Construct absolute path to systems.json
        if os.path.exists(system_file):
            try:
                with open(system_file, "r") as f:
                    systems = json.load(f).get("systems", {})
                    logging.debug(f"Loaded {len(systems)} predefined systems.")
                    return systems
            except Exception as e:
                logging.error(f"Failed to load systems.json: {e}")
                return {}
        else:
            logging.warning("systems.json not found.")
            return {}

    def write_systems(self):
        """Load predefined systems from systems.json."""
        script_dir = os.path.dirname(os.path.abspath(__file__))  # Get script's directory
        system_file = os.path.join(script_dir, "systems.json")  # Construct absolute path to systems.json
        try:
            with open(system_file, "w") as f:
                systems_json = { 'systems' : self.systems }
                json.dump(systems_json, f, indent=2)
                logging.debug(f"Wrote {system_file}")
        except Exception as e:
            logging.error(f"Failed to write systems.json: {e}")

    def do_reset(self):
        req = create_request(self.sid, 'reset')
        json_data = self.send_command(req)
        self.handle_response(json_data)

    def archive_conversation(self):
        req = create_request(self.sid, 'archive-conversation')
        json_data = self.send_command(req)
        self.handle_response(json_data)

    def new_s(self, sid, system=None):
        self.sid = sid
        req = create_request(sid, 'new-s', system=system)
        json_data = self.send_command(req)
        if self.handle_response(json_data):
            sys.exit(1)
        #set up history file once we confirm our sid
        self.history_file = os.path.join(self.config['settings']['dpath'], f"history-{self.sid}.txt")

    def use_s_query(self, sid, data):
        self.sid = sid
        req = create_request(self.sid, 'use-s-query', data, oneshot=self.oneshot)
        json_data = self.send_command(req)

        if self.handle_response(json_data):
            sys.exit(1)

    def use_s_system(self, system):
        req = create_request(self.sid, 'use-s-system', system=system, oneshot=self.oneshot)
        json_data = self.send_command(req)

        if self.handle_response(json_data):
            sys.exit(1)

    def rm_s(self, sid):
        self.sid = sid
        req = create_request(self.sid, 'rm-s', sid)
        json_data = self.send_command(req)

        if self.handle_response(json_data):
            sys.exit(1)

    def list_s(self):
        req = create_request(self.sid, 'list-s')
        json_data = self.send_command(req)

        if self.handle_response(json_data):
            sys.exit(1)

        print(json_data['data'])

    def list_sys(self):
        """List available predefined systems with their content."""
        if not self.systems:
            print("No predefined systems loaded.")
            return
        print("Available systems:")
        for name, data in self.systems.items():
            content = data.get("content", "[No content]")
            print(f"\n  - {name}:\n{content}")

    def get_system(self, system):
        """Use a predefined system from system.json"""
        if system not in self.systems:
            logging.error(f'{system} not supported')
            sys.exit(1)

        if system in ['code-generator', 'recipe-generator', 'modern-translator', 'code-commentor']:
            self.no_markdown = True

        return self.systems[system]['content']

    def use_sys(self, system, query):
        system_content = self.get_system(system)
        req = create_request(self.sid, 'use-sys', query, system=system_content, oneshot=self.oneshot)
        json_data = self.send_command(req)

        if self.handle_response(json_data):
            sys.exit(1)

    def list_models(self):
        req = create_request(self.sid, 'list-m')
        json_data = self.send_command(req)

        if self.handle_response(json_data):
            sys.exit(1)

        print(json_data['data'])

    def use_model(self, model):
        req = create_request(self.sid, 'use-model', model)
        json_data = self.send_command(req)

        if self.handle_response(json_data):
            sys.exit(1)

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
                    #self.do_user_content("show me the last response")

                elif input_text in ["h", "?"]:
                    self.show_help()  # ✅ Call the help menu function

                elif input_text.startswith("l "):
                    self.load_s(input_text[2:])

                elif input_text.startswith("s "):
                    self.save_session(input_text[2:])

                elif input_text == "e":
                    text = open_vim()
                    self.do_user_content(text)

                elif input_text == "":
                    pass  # Ignore empty input

                else:
                    self.do_user_content(input_text)

        except (EOFError, KeyboardInterrupt):
            save_history(self.history_file)
            print("\nExiting and saving history. Goodbye!")
            sys.exit(0)

    def add_system(self, system_name, system_content):
        if system_name in self.systems:
            logging.error(f'{system_name} exists: {self.systems[system_name]}')
            return

        self.systems[system_name] = {'role': 'system', 'content': system_content}

        logging.info(f'{system_name} added')

        self.write_systems()

    def rm_system(self, system_name):
        if not system_name in self.systems:
            logging.error(f'{system_name} does not exist')
            return

        del self.systems[system_name]

        logging.info(f'{system_name} removed')

        self.write_systems()



def handle_non_stdin(args, client):
    # Handle actions when no stdin input is provided.

    user_args = None
    if args.edit:
        user_args = open_vim()
    elif args.args:
        user_args = " ".join(args.args)

    if args.system:
        client.use_s_system(user_args)
    elif args.use_sys:
        client.server_init()
        client.use_sys(args.use_sys, user_args)
    elif user_args:
        if not args.use_s:
            client.server_init()
        client.do_user_content(user_args)
    else:
        logging.warning("⚠️  No valid action arguments provided.")

def handle_stdin(args, client):
        # Read from stdin, then choose an action.
        input_text = sys.stdin.read().strip()  # Remove trailing newlines/spaces
        if not input_text:
            logging.warning("⚠️  No input received from stdin.")
            sys.exit(1)  # Exit with a non-zero code if nothing is received
        else:
            # Optionally, log a truncated version of the input.
            logging.debug(f"📥 Received input from stdin: {input_text[:100]}...")

        client.server_init()

        # Process the stdin input based on additional flags
        if args.edit:
            client.server_init()
            user_args = open_vim()
            client.do_user_content(user_args)
            client.do_user_content(input_text)
        elif args.args:
            client.server_init()
            msg = " ".join(args.args)
            # Here, we send an introductory message followed by the actual input.
            client.do_user_content(f"I'm about to send text your way and I want you to {msg}")
            client.do_user_content(input_text)
        elif args.use_sys:
            client.server_init()
            client.use_sys(args.use_sys, input_text)
        else:
            client.server_init()
            client.do_user_content(input_text)


if __name__ == "__main__":
    from cli import parse_args
    args = parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    console = Console()
    #init(autoreset=True)
    init()

    sid = args.use_s[0] if args.use_s else None
    client = Client(sid=sid, no_markdown=args.no_markdown, save_responses=args.save_responses)

    if args.oneshot:
        client.oneshot=True

    if args.rm_s:
        client.rm_s(args.rm_s[0])
        sys.exit(0)
    elif args.list_s:
        client.list_s()
        sys.exit(0)
    elif args.list_sys:
        client.list_sys()
        sys.exit(0)
    elif args.list_m:
        client.list_models()
        sys.exit(0)
    elif args.new_s:
        system = " ".join(args.system) if args.system else None
        if args.use_sys:
            system = client.get_system(args.use_sys)
        client.new_s(args.new_s[0], system)
        sys.exit(0)
    elif args.init:
        client.server_init()
        sys.exit(0)
    elif args.exit:
        client.server_exit()
        sys.exit(0)
    elif args.model:
        client.server_init()
        client.use_model(args.model)
        sys.exit(0)
    elif args.reset:
        client.do_reset()
        sys.exit(0)
    elif args.interactive:
        client.load_history()
        client.go_interactive()
        sys.exit(0)
    elif args.archive_conversation:
        client.archive_conversation()
        sys.exit(0)
    elif args.add_system:
        if len(args.add_system) < 2:
            logging.error("Need content for --add-system")
            sys.exit(1)
        client.add_system(args.add_system[0], args.add_system[1])
        sys.exit(0)
    elif args.rm_system:
        client.rm_system(args.rm_system[0])
        sys.exit(0)


    if not args.stdin:
            handle_non_stdin(args, client)
    else:
            handle_stdin(args, client)
