import uuid
import json
import os
from custom_board_games.gen_text import gen_game_text
from custom_board_games.utils.redis import load_game_config


assert os.getenv("ENV", "test") == "test"


def test_gen_text():
    with open('test/fixtures/full_game_config.json') as f:
        loaded_config = json.load(f)
    game_run = str(uuid.uuid4())
    gen_game_text(game_run, "coup", "Angry Birds", verbose=False)
    config = load_game_config(game_run)
    assert config == loaded_config
