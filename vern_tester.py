#!/usr/bin/env python3

import sys
import config
import json


class Tester:

    def __init__(self):
        self.session_file_prefix = f"{config.dpath}/session-"
        self.sid = 1

        session_file = f"{self.session_file_prefix}{self.sid}"
        try:
            with open(session_file, 'r') as f:
                messages = [json.loads(line) for line in f]
        except json.decoder.JSONDecodeError as e:
            print("JSON Decode Error:")
            print(f"Message: {e.msg}")
            print(f"Document: {e.doc}")
            print(f"Position: {e.pos}")
            print(f"Line number: {e.lineno}, Column: {e.colno}")
if __name__ == '__main__':
    t = Tester()

