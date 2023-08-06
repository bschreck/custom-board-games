import json
import yaml
from .redis import load_game_config, save_game_config
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
        return cls._complete(content, "story-yaml", game_run)

    @classmethod
    def style_completion(cls, content, game_run):
        # TODO: character names in style need to match
        # coup characters instead of generating random words
        config = load_game_config(game_run)
        split_str = "STYLE TEMPLATE ----\n"
        content_prompt, content_template_str = content.split(split_str)
        content_template = json.loads(content_template_str)
        style_yaml_config = {"style-yaml": {}}
        for component in config["components"]["variants"]:
            if component["name"] == "Character Card":
                for i, variant in enumerate(component["variants"]):
                    style_yaml_config["style-yaml"][f"character{i+1}"] = {"name": variant["name"]}
                    if i > 1:
                        # THIS is such a hack
                        jsonstr = """{'{{character1.name}}_image': {'variant_name': '{{character1.name}}', 'prompt': '{{character1.name_prompt}}', 'types': ['character_image', 'component'], 'size_types': ['character_image']}, '{{character1.name}}_logo': {'variant_name': '{{character1.name}}', 'prompt': '{{character1.logo_prompt}}', 'types': ['character_image_logo', 'component'], 'size_types': ['character_image_logo']}}"""
                        jsonstr = jsonstr.replace("1", str(i + 1))
                        content_template["image_prompts"] = {**content_template["image_prompts"], **eval(jsonstr)}
                break
        content_template_str = json.dumps(content_template)
        content = content_prompt + split_str + content_template_str
        save_game_config(game_run, style_yaml_config)
        return cls._complete(content, "style-yaml", game_run)

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
