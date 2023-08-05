import json
import os
from custom_board_games.utils.format_template import MetaTemplateGenerator


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
        cls._complete(content, "narrative.yaml.jinja", game_run)

    @classmethod
    def style_completion(cls, content, game_run):
        cls._complete(content, "style.yaml.jinja", game_run)

    @classmethod
    def config_completion(cls, content, game_run):
        cls._complete(content, "config.yaml.jinja", game_run)

    @classmethod
    def _complete(cls, content, template_file, game_run):
        meta_gen = MetaTemplateGenerator(game_run, "src/custom_board_games/game_configs/coup", template_file)
        os.makedirs(cls.dirname, exist_ok=True)
        rendered_dict = meta_gen.render_for_mock(f"{cls.dirname}/{template_file.replace('.yaml.jinja', '-mock.yaml')}")
        return Completion(json.dumps(rendered_dict))
