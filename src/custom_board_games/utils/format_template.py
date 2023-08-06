from jinja2 import Environment, select_autoescape, FileSystemLoader
import yaml
import json
from .redis import load_key_from_game_config, save_nested_key_to_game_config, load_game_config, save_game_config
from redis.exceptions import ResponseError
from random_word import RandomWords
import random
import os

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

random_word_gen = RandomWords()

COLOR_HEX_REGEX = r"^([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
REGEXES = {
    "color_hex": COLOR_HEX_REGEX,
    # TODO
    # "webkit_gradient": rf"^(linear-gradient\(#{COLOR_HEX_REGEX}, #{COLOR_HEX_REGEX}\);)$",
    "webkit_gradient": "test",
}
EXAMPLE_REGEXES = {"color_hex": "#000000", "webkit_gradient": "linear-gradient(#e66465, #9198e5);"}


def in_jinja_braces(s):
    return "{{" + s + "}}"


def gen_color_hex():
    """generates a random 6 character hex color code"""
    return "".join([random.choice("0123456789ABCDEF") for _ in range(6)])


class MetaTemplateGenerator:
    def __init__(self, game_run, dirname, template_name):
        self.game_run = game_run
        self.dirname = dirname
        self.template_name = template_name
        self.template_file = os.path.join(dirname, f"{template_name.replace('-', '.')}.jinja")
        self.config = None

    def gen_random_bool(self):
        return random.randint(0, 1) == 1

    def gen_random_int(self, lo, hi):
        return random.randint(lo, hi)

    def gen_random_image_prompt(self):
        return self.gen_random_name(n=random.randint(4, 10))

    def gen_random_name(self, n=1):
        return " ".join([random_word_gen.get_random_word() for _ in range(n)])

    def type_generator(self, _type):
        return {
            "image_prompt": self.gen_random_image_prompt,
            "bool": self.gen_random_bool,
            "int": self.gen_random_int,
            "name": self.gen_random_name,
        }[_type]

    def gen_random_word_of_type(self, _type, *args):
        return self.type_generator(_type)(*args)

    def regex_filter_for_gpt(self, regex, *args):
        return in_jinja_braces(REGEXES[regex])

    def gen_random_regex_of_type(self, regex):
        if regex == "color_hex":
            return gen_color_hex()
        elif regex == "webkit_gradient":
            return EXAMPLE_REGEXES[regex]
        else:
            raise ValueError(f"Unknown regex {regex}")

    def regex_filter_for_mock(self, regex):
        return self.gen_random_regex_of_type(regex)

    def type_filter_for_gpt(self, _type, *args):
        return in_jinja_braces(_type)

    def type_filter_for_mock(self, _type, *args):
        return self.gen_random_word_of_type(_type, *args)

    def objkey_filter_for_gpt(self, key, _type, *args):
        # TODO: can optionally add type hints to gpt
        return in_jinja_braces(key)

    def load_objvalue_from_key(self, key):
        key_parts = key.split(".")
        objvalue = self.template
        for k in key_parts:
            if objvalue.get(k, None):
                objvalue = objvalue[k]
            else:
                return None
        return objvalue

    def objkey_filter_for_mock(self, key, _type, *args):
        print(key, _type, *args)
        objvalue = self.load_objvalue_from_key(key)
        if objvalue is None:
            print("no obj value, generating")
            objvalue = self.gen_random_word_of_type(_type, *args)
            self.save_nested_key_to_config(key, objvalue)
            return objvalue
        return objvalue

    @property
    def template(self):
        template = self.config.get(self.template_name, None)
        if template is None:
            self.config[self.template_name] = {}
        return self.config[self.template_name]

    def save_nested_key_to_config(self, key, value):
        key_parts = key.split(".")
        dict_to_save = self.template
        for k in key_parts[:-1]:
            if dict_to_save.get(k, None) is None:
                dict_to_save[k] = {}
            dict_to_save = dict_to_save[k]
        dict_to_save[key_parts[-1]] = value

    def render_for_gpt(self, output_file):
        self.config = load_game_config(self.game_run)
        env = Environment(loader=FileSystemLoader(searchpath="./"), autoescape=select_autoescape())
        env.filters["type"] = self.type_filter_for_gpt
        env.filters["regex"] = self.regex_filter_for_gpt
        env.filters["objkey"] = self.objkey_filter_for_gpt
        template = env.get_template(str(os.path.relpath(self.template_file)))
        rendered = template.render(**self.config)
        as_dict = yaml.load(rendered, Loader=Loader)
        with open(output_file, "w") as f:
            json.dump(as_dict, f, indent=4)
        return as_dict

    def render_for_mock(self, output_file):
        self.config = load_game_config(self.game_run)
        env = Environment(loader=FileSystemLoader(searchpath="./"), autoescape=select_autoescape())
        env.filters["type"] = self.type_filter_for_mock
        env.filters["regex"] = self.gen_random_regex_of_type
        env.filters["objkey"] = self.objkey_filter_for_mock
        with open(str(os.path.relpath(self.template_file))) as f:
            template_dict = yaml.load(f.read(), Loader=Loader)
        if self.template_name == "style-yaml":
            for component in self.config["components"]["variants"]:
                if component["name"] == "Character Card":
                    for i in range(len(component["variants"])):
                        if i > 1:
                            # THIS is such a hack
                            yamlstr = """
"{{'character1.name'|objkey('name', 1)}}_image":
  variant_name: "{{'character1.name'|objkey('name', 1)}}"
  prompt: "{{'character1.name_prompt'|objkey('image_prompt')}}"
  types: [character_image, component]
  size_types: [character_image]
"{{'character1.name'|objkey('name', 1)}}_logo":
  variant_name: "{{'character1.name'|objkey('name', 1)}}"
  prompt: "{{'character1.logo_prompt'|objkey('image_prompt')}}"
  types: [character_image_logo, component]
  size_types: [character_image_logo]
"""
                            # jsonstr = """{"{{'character1.name'}}_image": {"variant_name": "{{'character1.name'}}", "prompt": "{{'character1.name_prompt'}}", "types": ["character_image", "component"], "size_types": ["character_image"]}, "{{'character1.name'}}_logo": {"variant_name": "{{'character1.name'}}", "prompt": "{{'character1.logo_prompt'}}", "types": ["character_image_logo", "component"], "size_types": ["character_image_logo"]}}"""
                            # jsonstr = jsonstr.replace("1", str(i + 1))
                            yamlstr = yamlstr.replace("1", str(i + 1))

                            # template_dict["image_prompts"] = {**template_dict["image_prompts"], **json.loads(jsonstr)}
                            template_dict["image_prompts"] = {
                                **template_dict["image_prompts"],
                                **yaml.load(yamlstr, Loader=Loader),
                            }
                    break
        template_str = yaml.dump(template_dict, Dumper=Dumper).replace("''", "'")
        template = env.from_string(template_str)

        rendered = template.render(**self.config)
        as_dict = yaml.load(rendered, Loader=Loader)

        with open(output_file, "w") as f:
            f.write(rendered)
        return as_dict


if __name__ == "__main__":
    game_run = "test_game_run"
    meta_gen = MetaTemplateGenerator(game_run, "src/custom_board_games/game_configs/coup", "style-yaml")
    os.makedirs("tmp", exist_ok=True)
    meta_gen.render_for_mock("tmp/style-mock.yaml")
    meta_gen.render_for_gpt("tmp/style-gpt.json.jinja")
