import argparse
import config

def parse_args():
    parser = argparse.ArgumentParser(description='Send text to server.')
    parser.add_argument('-d', '--debug', action='store_true', help='Print debug messages')
    parser.add_argument('--new-s', type=str, nargs='+', help='Start a new session')
    parser.add_argument('--use-s', type=str, nargs=1, help='Use an existing session')
    parser.add_argument('--rm-s', type=str, nargs=1, help='Remove an existing session')
    parser.add_argument('--list-s', action='store_true', help='List existing sessions')
    parser.add_argument('--role', type=str, nargs='+', help='Give a role')
    parser.add_argument('-i', '--interactive', action='store_true', help='Drop to interactive prompt')
    parser.add_argument('--no-markdown', action='store_true', help='Display response as raw markdown')
    parser.add_argument('-s', '--save-responses', action='store_true', help='Save all responses as text', default=config.save_responses)
    parser.add_argument('--stdin', action='store_true', help='Read input from stdin and send to server')
    parser.add_argument('--message', type=str, nargs='+', help='Give a message for the input')
    parser.add_argument("args", nargs="*", help="Multiple positional arguments")
    parser.add_argument("--list-m", action='store_true', help='List available models')
    return parser.parse_args()
