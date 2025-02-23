#!/usr/bin/env python3

import os
import sys

from os.path import join

HOME=os.environ['HOME']
path = f'{HOME}/.config/vern-dev/'
dpath = f'{HOME}/.local/share/vern-dev/'
save_responses = True
server_info_file = join(path, 'server_info.txt')
