import logging
import openai
import os
import sys
import tiktoken

class AIHandler:
    def __init__(self, config):
        self.client = None
        self.init_ai()

        # Define the model's token limit
        self.TOKEN_LIMIT = 30000
        if config['settings']['model'] in ['gpt-4o-mini', 'gpt-3.5-turbo']:
            self.TOKEN_LIMIT = 200000

        self.config = config
        # Initialize tokenizer for GPT-4o
        self.ENCODER = tiktoken.encoding_for_model(self.config['settings']['model'])

    def init_ai(self):
        """ Initialize AI client """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logging.error("OPENAI_API_KEY is not set")
            sys.exit(1)

        self.client = openai.OpenAI(api_key=api_key)

    def count_tokens(self, messages):
        """Returns the number of tokens in a given text"""
        text = " ".join(msg["content"] for msg in messages if "content" in msg)
        return len(self.ENCODER.encode(text))

    def get_airesponse(self, session_context, oneshot_user_content=None):
        """ Generate AI response for given context """
        if not self.client:
            err_msg = "AI Client not initialized"
            logging.error(err_msg)
            return {"status": "error", "code": "client_not_initialized", "message": err_msg}

        ai_content = [session_context.system_content] + session_context.user_and_assistant_content
        if oneshot_user_content:
            ai_content = [session_context.system_content] + oneshot_user_content

        token_count = self.count_tokens(ai_content)

        if token_count > self.TOKEN_LIMIT:
            err_msg = f"Token limit exceeded: {token_count} > {self.TOKEN_LIMIT}"
            logging.error(err_msg)
            return {"status": "error", "code": "token_limit_exceeded", "message": err_msg}

        logging.debug(f"Tokens of message: {token_count}")

        logging.debug(f"Getting AI response for {ai_content}")

        try:
            return {
                "status": "success",
                "data": self.client.chat.completions.create(
                    model=session_context.config['settings']['model'],
                    messages=ai_content,
                    #temperature=0,
                    #max_completion_tokens=16384,
                    max_completion_tokens=50000,
                ),
            }
        except openai.AuthenticationError as e:
            logging.error(f"❌ OpenAI API authentication error: {e}")
            return {"status": "error", "code": "auth_error", "message": "Invalid OpenAI API key. Check your API key settings."}
        except openai.OpenAIError as e:
            logging.error(f"❌ OpenAI API request failed: {e}")
            return {"status": "error", "code": "api_error", "message": str(e)}

    def list_models(self):
        return openai.models.list()
