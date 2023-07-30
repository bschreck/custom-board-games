import json

class Choice:
    def __init__(self, message_str):
        self.message = {"role": "assistant", "content": message_str}
class Completion:
    def __init__(self, message_str):
        self.choices = [Choice(message_str)]
class ChatCompletion:
    def create(model, messages):
        content = messages[-1]["content"].split("---- TEMPLATE ----")[-1]
        json.loads(content)
        return Completion(content)
