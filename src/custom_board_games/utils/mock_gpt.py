import json
import re
from random_word import RandomWords


class Choice:
    def __init__(self, message_str):
        self.message = {"role": "assistant", "content": message_str}


class Completion:
    def __init__(self, message_str):
        self.choices = [Choice(message_str)]


class ChatCompletion:
    random_word_gen = RandomWords()

    @classmethod
    def create(cls, model, messages):
        content = messages[-1]["content"].split("---- TEMPLATE ----")[-1]
        pattern = r"<\b\w*\b>"
        unique_words = set(re.findall(pattern, content))
        mapping = {word: cls.random_word_gen.get_random_word() for word in unique_words}
        for word, random_word in mapping.items():
            content = content.replace(word, random_word)

        # make sure the returned content is valid json
        json.loads(content)
        return Completion(content)
