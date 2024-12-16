#!/usr/bin/env python3

from openai import OpenAI

import argparse
import json
import logging
import os
import pickle
import random
import re
import select
import socket
import sys
import time
import threading

from protocol import *
import config

class ClientContext:
    def __init__(self, cid, sid, model='gpt-4o', role={'role': 'system', 'content': 'You are a helpful assistant.'}):
        self.cid = cid
        self.sid = sid
        self.model = model
        self.session_file_prefix = f"{config.dpath}/session-"
        self.messages = [role]

        if not os.path.exists(config.dpath):
            os.mkdir(config.dpath)

    def validate_json(self, data):
        """
        Validate the structure of JSON data.
        This function can be customized to enforce specific JSON schemas.
        """
        required_keys = {"role", "content"}

        if not isinstance(data, dict):
            raise ValueError("Invalid JSON: Data is not a dictionary.")

        missing_keys = required_keys - data.keys()
        if missing_keys:
            raise ValueError(f"Invalid JSON: Missing keys: {', '.join(missing_keys)}")

        if not isinstance(data["role"], str) or not isinstance(data["content"], str):
            raise ValueError("Invalid JSON: 'role' and 'content' must be strings.")

    def load_session_messages(self):
        session_file = f"{self.session_file_prefix}{self.sid}"

        if not os.path.exists(session_file):
            logging.debug(f"Skipping loading {session_file}")
            return

        messages = []

        with open(session_file, 'r') as f:
            messages = [json.loads(line) for line in f]

        logging.debug(f'Loaded session messages {messages}')
        self.messages = messages

    def _append_session_file(self, new_message):
        session_file = f"{self.session_file_prefix}{self.sid}"
        with open(session_file, 'a') as f:
            json.dump(new_message, f)
            f.write('\n')

    def append_session_file(self, new_message):
        try:
            # Validate the new message
            self.validate_json(new_message)

            session_file = f"{self.session_file_prefix}{self.sid}"
            with open(session_file, 'a') as f:
                json.dump(new_message, f)
                f.write('\n')
        except ValueError as e:
            logging.error(f"Failed to append invalid JSON to session file: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error while appending JSON: {e}")
            raise

    def write_session_file(self):
        try:
            session_file = f"{self.session_file_prefix}{self.sid}"
            logging.debug(f"Writing {session_file}")
            with open(session_file, 'w') as f:
                for message in self.messages:
                    # Validate each message
                    self.validate_json(message)
                    json.dump(message, f)
                    f.write('\n')
        except ValueError as e:
            logging.error(f"Failed to write invalid JSON to session file: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error while writing JSON: {e}")
            raise

    def _write_session_file(self):
        session_file = f"{self.session_file_prefix}{self.sid}"
        logging.debug(f"Writing {session_file}")
        with open(session_file, 'a') as f:
            for message in self.messages:
                json.dump(message, f)
            f.write('\n')

    def new_message(self, role, content):
        new_message = {'role':role, 'content':content}
        self.messages.append(new_message)
        self.append_session_file(new_message)

    def __repr__(self):
        return f"ClientContext(cid={self.cid}, sid={self.sid}, model={self.model})"


class CommandListener:
    def __init__(self, model="gpt-4o"):
        self.host = 'localhost'  # Use localhost for simplicity
        self.port = self.find_available_port()
        self.running = False

        self.model = model
        logging.info(f"Using model {model}")
        self.init_ai()

        #ctxts stands for 'client contexts'
        self.ctxts = {}
        #limit to 1000 for now
        self.ctxts_max = 1000

        self.supported_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"]

    def search_by_key_part(self, dictionary, key_part, position):
        results = []
        for key, value in dictionary.items():
            if key[position] == key_part:
                results.append((key, value))
        logging.debug(f'Returning {results} for position {position}')
        return results

    def ctxt_find(self, cid=-1, sid=-1):
        results = self.search_by_key_part(self.ctxts, cid, 0)

        if len(results) == 1:
            logging.debug(f'Found ctxt by cid: {cid}')
            return results[0]
        elif len(results) > 1:
            logging.error(f'Found more than one ctxt')
            for result in results:
                print(result)

        results = self.search_by_key_part(self.ctxts, sid, 1)

        if len(results) == 0:
            return (None, None)
        elif len(results) == 1:
            logging.debug('Found ctxt by sid: {cid}')
            return results[0]
        else:
            logging.error("Found more than one ctxt")
            for result in results:
                print(result)

    def ctxt_create(self, json_data):

        cid = -1
        #generate client id
        while True:
            cid = random.randint(1, self.ctxts_max)
            if not cid in self.ctxts:
                break

        #logging.info(f"json_data: {json_data}")
        sid = json_data['sid']
        if sid == -1:
            sid = self.find_next_sid()

        logging.debug(f'Added client context cid {cid} sid {sid}')

        role = json_data['role']
        if role:
            role = {'role' : 'system', 'content' : role}
        else:
            role = {'role' : 'system', 'content' : 'Act as a helpful tech savvy assistant'}

        ctxt_new = ClientContext(cid, sid, json_data['model'], role)

        self.ctxts[(cid, sid)] = ctxt_new

        #don't try to load session if it does not exist
        if os.path.exists(f'{ctxt_new.session_file_prefix}{sid}'):
            ctxt_new.load_session_messages()
        return ctxt_new

    def get_ctxt(self, cid):
        return self.ctxts.get(cid)

    def remove_ctxt(self, cid):
        if cid in self.ctxts:
            del self.ctxts[cid]

    def find_all_sids(self, directory='.'):
        """
        Find all existing session IDs based on session files in the specified directory.

        Parameters:
        - directory (str): The directory to search for session files. Defaults to the current directory.

        Returns:
        - list: A list of existing session IDs.
        """
        # Find session files matching the pattern 'session-<number>'
        logging.debug(f'Looking for sids in {directory}')
        session_files = [f for f in os.listdir(directory) if re.match(r'^session-[a-zA-Z0-9]+$', f)]

        if session_files:
            # Extract numerical IDs from session filenames
            sids = [re.search(r'session-([a-zA-Z0-9]+)', f).group(1) for f in session_files]
            return sids
        else:
            # No session files found, return an empty list
            return []


    def find_next_sid(self):
        # Find the next available session ID based on existing session files
        session_files = [f for f in os.listdir() if re.match(r'^.session-\d+$', f)]
        if session_files:
            sids = [int(re.search(r'\d+', f).group()) for f in session_files]
            return max(sids) + 1
        else:
            return 1

    def do_apikey(self):

        if 'APIKEY' in os.environ:
            self.apikey = os.environ['APIKEY']
        else:
            logging.error("set APIKEY environment variable")
            sys.exit(1)

    def init_ai(self):
        logging.debug("Initializing AI")
        self.do_apikey()
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", self.apikey))

    def get_airesponse(self, ctxt):
        logging.debug(f"Getting response for {ctxt.messages}")
        current_level = logging.getLogger().getEffectiveLevel()
        logging.getLogger().setLevel(logging.CRITICAL)
        self.response = self.client.chat.completions.create(
            model=ctxt.model,
            messages=ctxt.messages,
            temperature=0,
        )
        logging.getLogger().setLevel(current_level)
        return self.response

    def find_available_port(self):
        # Let the OS choose an available port by setting port to 0
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temp_socket:
            temp_socket.bind(('localhost', 0))
            return temp_socket.getsockname()[1]

    def start(self):
        self.running = True
        self.start_server_thread()
        self.write_server_info_to_file()

    def start_server_thread(self):
        server_thread = threading.Thread(target=self.server_thread)
        server_thread.start()

    def server_thread(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen()

            logging.info(f"Vern server listening on {self.host}:{self.port}")
            while self.running:
                # Use select to check for incoming connections
                readable, _, _ = select.select([server_socket], [], [], 0.1)
                for sock in readable:
                    if sock == server_socket:
                        client_socket, _ = server_socket.accept()
                        client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                        client_thread.start()
            logging.debug(f"Vern server exiting")

    def send_ack(self, ctxt, client_socket):
        ack = create_response(ctxt.cid, ctxt.sid, 'ack', 'affirmative', 'roger')
        self.send_response(client_socket, ack)

    def send_nack(self, ctxt, client_socket, reason):
        nack = create_response(ctxt.cid, ctxt.sid, 'nack', reason, 'did not work')
        self.send_response(client_socket, nack)

    def send_response(self, client_socket, response):
        l = len(response)
        client_socket.sendall(l.to_bytes(4, byteorder='big'))
        client_socket.sendall(response.encode())

    def send_obj(self, client_socket, obj):
        l = len(obj)
        client_socket.sendall(l.to_bytes(4, byteorder='big'))
        client_socket.sendall(obj)

    def dump(self):
        print("Dumping client contexts")

        for cid in self.ctxts:
            print("***********************************************************************************************")
            print(f"Context {cid} model: {self.ctxts[cid].model} session: {self.ctxts[cid].sid}")
            for message in self.ctxts[cid].messages:
                print(message)
            print("***********************************************************************************************")

    def set_model(self, ctxt, model):
        if model not in self.supported_models:
            return False
        ctxt.model = model
        return True

    def handle_client(self, client_socket):
        tid = threading.get_ident()
        with client_socket:

            json_data = recv_json(client_socket)

            cid = json_data['cid']
            sid = json_data['sid']
            cmd = json_data['cmd']
            text = json_data['text']
            role = json_data['role']

            logging.debug(f"got json_data {json_data}")

            logging.debug(f'Searching for context cid:{cid} sid:{sid}')
            ctxt_tuple = self.ctxt_find(cid, sid)
            ctxt = ctxt_tuple[1]

            if ctxt == None:
                logging.debug(f'Creating context {json_data}')
                ctxt = self.ctxt_create(json_data)

            logging.debug(ctxt)

            try:

                if cmd == 'init':
                    ctxt.write_session_file()
                    response = create_response(ctxt.cid, ctxt.sid, 'success', 'none', 'none')
                    self.send_response(client_socket, response)
                    return

                elif cmd == 'new-s':
                    session_file = os.path.join(config.dpath, f'session-{text}')
                    if os.path.exists(session_file):
                        logging.debug(f'Session exists, sending nack')
                        self.send_nack(ctxt, client_socket, f'session-{text} exists')
                        return

                    logging.debug(f"Starting new session {text}")
                    #print(ctxt)
                    ctxt.write_session_file()
                    self.send_ack(ctxt, client_socket)

                    return

                elif cmd == 'use-s':
                    session_file = os.path.join(config.dpath, f'session-{text}')
                    if not os.path.exists(session_file):
                        logging.debug(f'Session {session_file} DOES NOT exist, sending nack')
                        self.send_nack(ctxt, client_socket, f'session-{text} DOES NOT exist')
                        return

                    logging.debug(f"Using existing session {session_file}")
                    ctxt.sid = text
                    ctxt.load_session_messages()
                    self.send_ack(ctxt, client_socket)
                    return

                elif cmd == 'replay-s':
                    session_file = os.path.join(config.dpath, f'session-{text}')
                    if not os.path.exists(session_file):
                        logging.debug(f'Session {session_file} DOES NOT exist, sending nack')
                        self.send_nack(ctxt, client_socket, f'session-{text} DOES NOT exist')
                        return

                    logging.debug(f"Replaying existing session {text}")
                    ctxt.sid = f"{text}"
                    ctxt.load_session_messages()

                    airesponse = self.get_airesponse(ctxt)

                    for choice in airesponse.choices:
                        logging.debug(choice.message.content)

                    my_response = create_response(ctxt.cid, ctxt.sid, 'success', 'airesponsetofollow', 'nah')
                    self.send_response(client_socket, my_response)

                    #send pickled response
                    obj = pickle.dumps(airesponse)
                    self.send_obj(client_socket, obj)
                    return

                elif cmd == 'load-s':
                    session_file = os.path.join(config.dpath, f'session-{text}')
                    if not os.path.exists(session_file):
                        logging.debug(f'Session {session_file} DOES NOT exist, sending nack')
                        self.send_nack(ctxt, client_socket, f'session-{text} DOES NOT exist')
                        return

                    logging.info(f"Loading existing session {text}")
                    ctxt.sid = f"{text}"
                    ctxt.load_session_messages()
                    self.send_ack(ctxt, client_socket)
                    return

                elif cmd == 'new-r':
                    logging.debug(f"Setting system role to {text}")
                    ctxt.new_message('system', text)
                    self.send_ack(ctxt, client_socket)
                    return

                elif cmd == 'query':

                    ctxt.new_message('user', text)

                    airesponse = self.get_airesponse(ctxt)
                    ctxt.new_message("assistant", airesponse.choices[0].message.content)

                    for choice in airesponse.choices:
                        logging.debug(choice.message.content)

                    my_response = create_response(ctxt.cid, ctxt.sid, 'success', 'airesponsetofollow', 'nah')
                    self.send_response(client_socket, my_response)

                    #send pickled response
                    obj = pickle.dumps(airesponse)
                    self.send_obj(client_socket, obj)
                    return

                elif cmd == 'model':
                    ret = self.set_model(ctxt, text)
                    if ret:
                        self.send_ack(ctxt, client_socket)
                    else:
                        self.send_nack(ctxt, client_socket, "failed to set model")
                    return


            except ValueError as v:
                print(v)
                print("Invalid command format")

        logging.debug(f"T{tid} Connection to client lost")

    def write_server_info_to_file(self):
        os.makedirs(config.path, exist_ok=True)
        server_info_file = f"{config.path}/server_info.txt"
        with open(server_info_file, 'w') as f:
                f.write(f"{self.host}\n{self.port}")

    def stop(self):
        self.running = False
        # Implement logic to gracefully shutdown server and client threads

def main():

    parser = argparse.ArgumentParser(description='Listen for commands from client')
    parser.add_argument('-d', '--debug', action='store_true', help='Print debug messages')
    parser.add_argument('-i', '--interactive', action='store_true', help='Print debug messages')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    command_listener = CommandListener()
    command_listener.start()

    try:
        while True:
            if args.interactive:
                command = input("Enter 'q' to quit: ")
                if command.lower() == 'q':
                    command_listener.stop()
                    break
                elif command.lower() == 'd':
                    command_listener.dump()
            else:
                time.sleep(.1)
    except KeyboardInterrupt:
        command_listener.stop()

if __name__ == "__main__":
    main()
