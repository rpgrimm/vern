import atexit
import json
import logging
import os
import pprint
import shutil


from utils import load_config

class SessionContext:
    DEFAULT_SYSTEM_CONTENT = (
        "You are a highly knowledgeable and tech-savvy assistant, specializing in programming, Linux, AI, open-source software, and Bitcoin. "
        "You provide clear, concise, and accurate responses while adapting to the user's level of expertise. "
        "If the user asks for coding help, you provide well-structured examples and explanations. "
        "For troubleshooting, you guide the user step-by-step. "
        "You value efficiency but ensure clarity in all responses."
    )

    @staticmethod
    def session_exists(dpath, sid):
        if sid.startswith('ppid'):
            dpath = os.path.join(dpath, '.ppid')
        exists = os.path.exists(os.path.join(dpath, f"session-{sid}"))
        isdir = os.path.isdir(os.path.join(dpath, f"session-{sid}"))

        if exists and not isdir:
            logging.error('Session is a file not a dir')

        return exists and isdir

    def remove_session(self, temp_dir, dpath, sid):
        trash_dir = os.path.join(temp_dir, "trash")
        os.makedirs(trash_dir, exist_ok=True)  # ✅ Ensure trash directory exists

        # ✅ Generate unique trash filename (session-name, session-name-1, session-name-2, etc.)
        base_name = f"session-{sid}"
        trash_path = os.path.join(trash_dir, base_name)
        counter = 0

        while os.path.exists(trash_path):
            counter += 1
            trash_path = os.path.join(trash_dir, f"{base_name}-{counter}")

        # ✅ Move session to trash
        shutil.move(self.session_dir, trash_path)
        logging.info(f"Moved session {sid} to trash as {os.path.basename(trash_path)}")

    def __init__(self, sid, config=None, model='gpt-4o-mini', system_content=None, ppid=False):
        self.sid = sid
        self.model = model
        self.user_and_assitant_content = []  # Stores user and assistant content in order

        if self.sid.startswith('ppid'):
            ppid=True

        if config is None:
            script_path = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_path, "config.yaml")
            config = load_config(config_path)

        self.session_dir = os.path.join(config['settings']['dpath'], f'session-{self.sid}')
        if ppid:
            self.session_dir = os.path.join(config['settings']['dpath'], '.ppid', f'session-{self.sid}')

        # File paths
        self.system_file = os.path.join(self.session_dir, "system.json")
        self.conversation_file = os.path.join(self.session_dir, "conversation.json")
        self.model_file = os.path.join(self.session_dir, "model")

        # Load existing session or initialize new one
        if self.session_exists(config['settings']['dpath'], sid):
            logging.info(f'Loading session from {self.session_dir}')
            self.load_session()
        else:
            logging.info(f'Creating {self.session_dir}')
            os.makedirs(self.session_dir, exist_ok=True)
            self.system_content = {
                "role": "system",
                "content": system_content if system_content else self.DEFAULT_SYSTEM_CONTENT
            }
            self.user_and_assistant_content = []  # Initialize empty conversation history
            self.save_session()  # Ensure initial system message is saved

        # Register exit handler to save session
        atexit.register(self.save_session)

    def load_session(self):
        """Load system message and conversation from files."""
        with open(self.system_file, "r") as f:
            self.system_content = json.load(f)

        with open(self.conversation_file, "r") as f:
            self.user_and_assistant_content = json.load(f)

        with open(self.model_file, "r") as f:
            self.model = f.read()

    def save_session(self):
        """Save the system message and conversation together."""
        with open(self.system_file, "w") as f:
            json.dump(self.system_content, f, indent=4)

        with open(self.conversation_file, "w") as f:
            json.dump(self.user_and_assistant_content, f, indent=4)

        with open(self.model_file, "w") as f:
            f.write(self.model)

    def add_user_content(self, content):
        """Add a new message to the conversation and save session."""
        message = {'role': 'user', "content": content}
        self.user_and_assistant_content.append(message)
        self.save_session()

    def add_assistant_content(self, content):
        """Add a new message to the conversation and save session."""
        message = {'role': 'assistant', "content": content}
        self.user_and_assistant_content.append(message)
        self.save_session()

    def get_user_and_assistant_content(self):
        """Retrieve all user-assistant messages, preserving order."""
        return self.user_and_assistant_content

    def set_system_content(self, new_system_content):
        """Update the system message and save session."""
        self.system_content = {'role': 'system', 'content': new_system_content}
        self.save_session()

    def get_system_content(self):
        return self.system_content['content']

    def add_oneshot_content(self, ai_text_response):
        """Save AI response as a one-shot file in session_dir/oneshot-X.json."""
        base_name = "oneshot"
        counter = 1
        oneshot_path = os.path.join(self.session_dir, f"{base_name}-{counter}.json")

        # Increment filename if it already exists
        while os.path.exists(oneshot_path):
            counter += 1
            oneshot_path = os.path.join(self.session_dir, f"{base_name}-{counter}.json")

        # Save the AI response
        with open(oneshot_path, "w") as f:
            json.dump({"role": "assistant", "content": ai_text_response}, f, indent=4)

        logging.info(f"Saved one-shot response to {os.path.basename(oneshot_path)}")

    def set_model(self, model):
        self.model = model
        self.save_session()

    def reset(self, sid):
        logging.info(f'Resetting {sid}')
        self.user_and_assistant_content = []
        self.save_session()
