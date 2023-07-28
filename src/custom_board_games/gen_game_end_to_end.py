import sys
import uuid
from gen_text import gen_game_text
from gen_images import gen_images_from_config_file
from utils.process_template import render
import fire
from config import GENERATED_OUTPUT_CONFIG_DIR
import os
from dotenv import load_dotenv
import redis

load_dotenv()


def gen_game(existing_game_name: str, theme: str):
    r = redis.Redis(host=os.getenv("REDIS_HOST", 'localhost'), port=os.getenv("REDIS_PORT", "6379"), db=0)
    game_run = str(uuid.uuid4())
    game_runs = r.json().get('game_runs', '.')
    game_run_doc = {'name': existing_game_name, 'theme': theme}
    if not game_runs:
        r.json().set('game_runs', '.', {game_run: game_run_doc})
    else:
        r.json().set('game_runs', f'.{game_run}', game_run_doc)
    game_runs = r.json().get('game_runs', '.')
    print(game_runs)
    
    gen_game_text(game_run, existing_game_name, theme, verbose=True)
    gen_images_from_config_file(game_run, verbose=True)

    #generated_game_config_file = os.path.join(GENERATED_OUTPUT_CONFIG_DIR, game_run, 'game_config.yaml')
    #generated_game_style_file = os.path.join(GENERATED_OUTPUT_CONFIG_DIR, game_run, 'art_text.yaml')
    #template_file = f'html_templates/{existing_game_name}.jinja'
    #output_file = f'html_rendered/{game_run}.html'
    #render(generated_game_config_file, generated_game_style_file, template_file, output_file)
    ## TODO: need to map image paths to generated_game_style_file
    ## and update jinja template to use that file's format


if __name__ == '__main__':
    fire.Fire(gen_game)
