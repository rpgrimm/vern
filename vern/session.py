import os
import json
import logging
import config
import pprint

class ClientContext:
    def __init__(self, cid, sid, model='gpt-4o', role=None):
        self.cid = cid
        self.sid = sid
        self.model = model
        self.session_file = os.path.join(config.dpath, f"session-{self.sid}")  # ✅ Use `session-{sid}` format 
        self.messages = [{'role': 'system', 'content': role}] if role else [{'role': 'system', 'content': 'You are a tech savvy helpful assistant.'}]

        os.makedirs(config.dpath, exist_ok=True)

    def __repr__(self):
        """Returns a detailed string representation of the object (for debugging)."""
        return f"ClientContext(cid={self.cid}, sid={self.sid}, model='{self.model}', messages={len(self.messages)} stored messages)"

    def __str__(self):
        """Pretty prints all the values when print(ctxt) is used."""
        data = {
            "Client ID": self.cid,
            "Session ID": self.sid,
            "Model": self.model,
            "Messages": self.messages
        }
        return pprint.pformat(data, indent=2, width=80)  # Pretty format with indentation


    def validate_json(self, data):
        """ Validate JSON structure """
        required_keys = {"role", "content"}
        if not isinstance(data, dict) or not required_keys.issubset(data.keys()):
            raise ValueError(f"Invalid JSON structure: {data}")

    def load_session_messages(self):
        """ Load session messages from file """
        if not os.path.exists(self.session_file):
            logging.debug(f"Skipping loading {self.session_file}, does not exist")
            return

        try:
            with open(self.session_file, 'r') as f:
                self.messages = [json.loads(line) for line in f]
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in session file: {e}")

    def write_session_file(self):
        """ Write session messages to file """
        with open(self.session_file, 'w') as f:
            for message in self.messages:
                json.dump(message, f)
                f.write('\n')

    def new_message(self, role, content):
        """ Add new message to session """
        new_message = {'role': role, 'content': content}
        self.messages.append(new_message)
        self.write_session_file()
