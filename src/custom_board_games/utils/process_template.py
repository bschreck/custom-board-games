from jinja2 import Environment, select_autoescape, FileSystemLoader
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

    
def render(input_config_file, input_style_file, template_file, output_file):
    with open(input_config_file, "r") as f:
        input_config = yaml.load(f, Loader=Loader)
    with open(input_style_file, "r") as f:
        input_style = yaml.load(f, Loader=Loader)

    env = Environment(
        loader=FileSystemLoader(searchpath="./"),
        autoescape=select_autoescape()
    )
    template = env.get_template(template_file)
    with open(output_file, "w") as f:
        f.write(template.render(**{**input_config, **input_style}))
     