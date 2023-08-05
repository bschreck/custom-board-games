from jinja2 import Environment, select_autoescape, FileSystemLoader
import yaml
import json
from .redis import load_key_from_game_config, save_nested_key_to_game_config, load_game_config
from redis.exceptions import ResponseError
from random_word import RandomWords
import random
import os

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

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
        self.template_file = os.path.join(dirname, f"{template_name}.jinja")

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
        try:
            return load_key_from_game_config(self.game_run, f"{self.template_name}.{key}")
        except ResponseError:
            return None

    def objkey_filter_for_mock(self, key, _type, *args):
        objvalue = self.load_objvalue_from_key(key)
        if objvalue is None:
            objvalue = self.gen_random_word_of_type(_type, *args)
            save_nested_key_to_game_config(self.game_run, f"{self.template_name}.{key}", objvalue)

            return objvalue

    def render_for_gpt(self, output_file):
        config = load_game_config(self.game_run)
        env = Environment(loader=FileSystemLoader(searchpath="./"), autoescape=select_autoescape())
        env.filters["type"] = self.type_filter_for_gpt
        env.filters["regex"] = self.regex_filter_for_gpt
        env.filters["objkey"] = self.objkey_filter_for_gpt
        template = env.get_template(str(os.path.relpath(self.template_file)))
        rendered = template.render(**config)
        print(rendered)
        as_dict = yaml.load(rendered, Loader=Loader)
        with open(output_file, "w") as f:
            json.dump(as_dict, f, indent=4)

    def render_for_mock(self, output_file):
        config = load_game_config(self.game_run)
        env = Environment(loader=FileSystemLoader(searchpath="./"), autoescape=select_autoescape())
        env.filters["type"] = self.type_filter_for_mock
        env.filters["regex"] = self.gen_random_regex_of_type
        env.filters["objkey"] = self.objkey_filter_for_mock
        template = env.get_template(str(os.path.relpath(self.template_file)))
        with open(output_file, "w") as f:
            f.write(template.render(**config))


if __name__ == "__main__":
    game_run = "test_game_run"
    meta_gen = MetaTemplateGenerator(game_run, "src/custom_board_games/game_configs/coup", "style.yaml")
    os.makedirs("tmp", exist_ok=True)
    meta_gen.render_for_mock("tmp/style-mock.yaml")
    meta_gen.render_for_gpt("tmp/style-gpt.json.jinja")
