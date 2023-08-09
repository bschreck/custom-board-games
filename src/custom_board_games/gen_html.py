from jinja2 import Environment, select_autoescape, FileSystemLoader
import os
from .utils.redis import load_game_config, save_game_config
from .config import HTML_TEMPLATES_DIR
from .gen_images import IMAGES_BY_NAME_KEY, IMAGES_BY_NAME_KEY_SCALED
import uuid
import fire


def gen_image_class(config, scaled=False):
    def image_class(variant):
        # TODO actually save classes in config
        return "image-class"

    return image_class


def gen_image_source(config, scaled=False):
    images_by_name_key = IMAGES_BY_NAME_KEY_SCALED if scaled else IMAGES_BY_NAME_KEY

    def image_source(variant):
        char = variant["characters"][0]
        return config[images_by_name_key][f"{char}_image_with_logo"]["image_paths"][0]

    return image_source


def gen_action_section(env, config, scaled=False):
    images_by_name_key = IMAGES_BY_NAME_KEY_SCALED if scaled else IMAGES_BY_NAME_KEY
    # TODO: rel file handling
    template = env.get_template("src/custom_board_games/html_templates/actions.jinja")

    def action_section(section):
        formatted_action_section_config = {
            "overview": section,
            "action_types": config["actions"]["action_types"],
            "images_by_name": config[images_by_name_key],
        }
        return template.render(**formatted_action_section_config)

    return action_section


def gen_components_section(env, config, scaled=False):
    template = env.get_template("src/custom_board_games/html_templates/components.jinja")
    images_by_name_key = IMAGES_BY_NAME_KEY_SCALED if scaled else IMAGES_BY_NAME_KEY

    def components_section(section):
        return template.render({**section, **config["components"], **{"images_by_name": config[images_by_name_key]}})

    return components_section


def gen_normal_section(env, config, scaled=False):
    template = env.get_template("src/custom_board_games/html_templates/normal.jinja")
    images_by_name_key = IMAGES_BY_NAME_KEY_SCALED if scaled else IMAGES_BY_NAME_KEY

    def normal_section(section):
        return template.render({**section, **{"images_by_name": config[images_by_name_key]}})

    return normal_section


def render(input_config, template_file, output_file, scaled=False):
    env = Environment(loader=FileSystemLoader(searchpath="./"), autoescape=select_autoescape())
    env.filters["image_class"] = gen_image_class(input_config, scaled=scaled)
    env.filters["image_source"] = gen_image_source(input_config, scaled=scaled)
    env.filters["action_section"] = gen_action_section(env, input_config, scaled=scaled)
    env.filters["components_section"] = gen_components_section(env, input_config, scaled=scaled)
    env.filters["normal_section"] = gen_normal_section(env, input_config, scaled=scaled)
    template = env.get_template(str(os.path.relpath(template_file)))
    with open(output_file, "w") as f:
        f.write(template.render(**input_config))


def get_template_file_from_config(config):
    return HTML_TEMPLATES_DIR / f"{config['original_game_name']}.jinja"


def gen_html_from_game_run(game_run, output_file):
    config = load_game_config(game_run)
    template_file = get_template_file_from_config(config)
    render(config, template_file, output_file)
    config["rendered_html"] = output_file
    save_game_config(game_run, config)


def main(output_file, game_run=None):
    if game_run is None:
        game_run = str(uuid.uuid4())
        print("Game run:", game_run)
    gen_html_from_game_run(game_run, output_file)


if __name__ == "__main__":
    fire.Fire(main)
