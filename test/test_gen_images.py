import json
import os
from custom_board_games.gen_text import gen_game_text
from custom_board_games.gen_images import gen_images_from_game_run
from custom_board_games.utils.redis import load_game_config


assert os.getenv("ENV", "test") == "test"


def test_gen_images(cleared_game_run):
    with open('test/fixtures/full_game_config_with_images.json') as f:
        loaded_config = json.load(f)
    gen_game_text(cleared_game_run, "coup", "Angry Birds", verbose=False)
    gen_images_from_game_run(cleared_game_run, nthreads=1)
    config = load_game_config(cleared_game_run)
    assert config == loaded_config
