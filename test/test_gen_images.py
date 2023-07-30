import json
import os
from custom_board_games.gen_text import gen_game_text
from custom_board_games.gen_images import gen_images_from_game_run
from custom_board_games.utils.redis import load_game_config


assert os.getenv("ENV", "test") == "test"


def test_gen_images(cleared_game_run):
    with open('test/fixtures/full_game_config_with_images.json') as f:
        loaded_config = json.load(f)
    gen_game_text(cleared_game_run, "coup", "Angry Birds", verbose=True)
    gen_images_from_game_run(cleared_game_run, nthreads=1)
    config = load_game_config(cleared_game_run)
    with open('test/fixtures/full_game_config_with_images2.json', 'w') as f:
        json.dump(config, f, indent=4)
    assert config == loaded_config

# TODO: image_paths and source_images (in a dict, instead of just list) in all top level images_by_name except the one that has it already
