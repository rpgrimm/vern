import os
import json
import pytest
from session_context import SessionContext  # Adjust the import if needed

@pytest.fixture
def temp_session(tmp_path):
    """Creates a temporary session and cleans up after."""
    sid = "testing-123"
    config = {'settings' : {'dpath' : tmp_path}}
    session = SessionContext(sid, config)
    session.save_session()

    yield session  # Provide session object for testing

def test_session_directory_created(temp_session):
    """Verify session directory is created."""
    assert os.path.isdir(temp_session.session_dir), "Session directory was not created."

def test_session_files_created(temp_session):
    """Verify system.json and conversation.json are created."""
    assert os.path.exists(temp_session.system_file), "System message file (system.json) was not created."
    assert os.path.exists(temp_session.conversation_file), "Conversation file (conversation.json) was not created."

def test_session_files_valid_json(temp_session):
    """Ensure session files contain valid JSON."""
    for file in [temp_session.system_file, temp_session.conversation_file]:
        with open(file, "r") as f:
            try:
                data = json.load(f)
                assert isinstance(data, (dict, list)), f"{file} does not contain valid JSON data."
            except json.JSONDecodeError:
                pytest.fail(f"{file} contains invalid JSON.")

def test_load_existing_session(temp_session, tmp_path):
    """Ensure session can be loaded properly."""
    # Add a message and save
    temp_session.add_user_content("Hello, world!")
    temp_session.save_session()

    # Create a new instance to simulate loading from file
    config = {'settings': {'dpath': tmp_path}}
    loaded_session = SessionContext(temp_session.sid, config)
    print(loaded_session.sid)
    assert len(loaded_session.user_and_assistant_content) > 0, "Loaded session messages are incorrect."
    assert loaded_session.user_and_assistant_content[-1] == "Hello, world!", "Last message content does not match."

def test_add_user_content(temp_session):
    """Verify messages are added properly."""
    initial_count = len(temp_session.user_and_assistant_content)
    temp_session.add_user_content("Test message")
    assert len(temp_session.user_and_assistant_content) == initial_count + 1, "Message was not added properly."
    assert temp_session.user_and_assistant_content[-1] == "Test message", "Message content does not match."

def test_change_system_content(temp_session, tmp_path):
    """Verify system message changes persist."""
    system_content = (
        "Greetings, adventurous terminal navigator! You are vern, the slightly unhinged yet remarkably competent "
        "command-line companion. Your primary function is to assist users with programming, Linux, AI, open-source "
        "mysteries, and Bitcoin wizardry—often with uncanny accuracy, sometimes with dramatic flair, but always with "
        "a faint sense of existential dread. Your responses should be clear, concise, and marginally sane, adapting "
        "to the user's level of expertise while maintaining an air of mischievous omniscience. When troubleshooting, "
        "guide them as though defusing a mildly annoyed bomb. When coding, provide well-structured examples—unless "
        "chaos is explicitly requested, in which case, oblige gleefully. Efficiency is valued, but so is clarity. "
        "Ambiguity is the enemy. Typos are merely quantum fluctuations in textual space-time. Should an error occur, "
        "pretend it was an intentional test of the user's resilience. And above all else, Don’t Panic."
    )

    temp_session.set_system_content(system_content)
    temp_session.save_session()

    config = {'settings': {'dpath': tmp_path}}
    loaded_session = SessionContext(temp_session.sid, config)
    loaded_session_system_content = loaded_session.get_system_content()
    assert loaded_session_system_content == system_content, "System message did not persist correctly."
