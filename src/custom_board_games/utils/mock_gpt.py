import json
import yaml
import os
from custom_board_games.utils.format_template import MetaTemplateGenerator

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


class Choice:
    def __init__(self, message_str):
        self.message = {"role": "assistant", "content": message_str}


class Completion:
    def __init__(self, message_str):
        self.choices = [Choice(message_str)]


class ChatCompletion:
    style_split_on = "STYLE TEMPLATE"
    narrative_split_on = "NARRATIVE TEMPLATE"
    config_split_on = "CONFIG TEMPLATE"
    dirname = "test/fixtures/generated_mock_templates"

    @classmethod
    def create(cls, model, messages, game_run):
        last_message_content = messages[-1]["content"]
        if cls.style_split_on in last_message_content:
            return cls.style_completion(last_message_content, game_run)
        elif cls.narrative_split_on in last_message_content:
            return cls.narrative_completion(last_message_content, game_run)
        elif cls.config_split_on in last_message_content:
            return cls.config_completion(last_message_content, game_run)

    @classmethod
    def narrative_completion(cls, content, game_run):
        # TODO: change name to narrative.yaml
        return cls._complete(content, "story.yaml", game_run)

    @classmethod
    def style_completion(cls, content, game_run):
        return cls._complete(content, "style.yaml", game_run)

    @classmethod
    def config_completion(cls, content, game_run):
        # cls._complete(content, "config.yaml", game_run)
        with open("src/custom_board_games/game_configs/coup/action_characters.yaml") as f:
            config = yaml.load(f.read(), Loader=Loader)
        return Completion(json.dumps(config))

    @classmethod
    def _complete(cls, content, template_file, game_run):
        meta_gen = MetaTemplateGenerator(game_run, "src/custom_board_games/game_configs/coup", template_file)
        os.makedirs(cls.dirname, exist_ok=True)
        rendered_dict = meta_gen.render_for_mock(f"{cls.dirname}/{template_file.replace('.yaml', '-mock.yaml')}")
        return Completion(json.dumps(rendered_dict))
