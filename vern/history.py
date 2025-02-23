import readline
import os

def load_history(history_file):
    if os.path.exists(history_file):
        with open(history_file, 'r') as file:
            history = file.read().splitlines()
        for line in history:
            readline.add_history(line)

def save_history(history_file):
    history = [readline.get_history_item(i) for i in range(1, readline.get_current_history_length() + 1)]
    # Don't save empty history
    if len(history) == 0:
        return
    with open(history_file, 'w') as file:
        file.write('\n'.join(history))

