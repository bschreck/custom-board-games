from jinja2 import Environment, select_autoescape, FileSystemLoader
from .utils.redis import load_game_config, save_game_config
from .config import HTML_TEMPLATES_DIR

    
def render(input_config, template_file, output_file):
    env = Environment(
        loader=FileSystemLoader(searchpath="./"),
        autoescape=select_autoescape()
    )
    template = env.get_template(template_file)
    with open(output_file, "w") as f:
        f.write(template.render(**{**input_config}))
     

def get_template_file_from_config(config):
    return HTML_TEMPLATES_DIR / f"{config['original_game_name']}.jinja"
    

def render_from_game_run(game_run, output_file):
    config = load_game_config(game_run)
    template_file = get_template_file_from_config(config)
    render(config, template_file, output_file)
    config["rendered_html"] = output_file
    save_game_config(game_run, config)