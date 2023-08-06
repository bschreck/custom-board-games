import json
import os
from custom_board_games.utils.redis import load_game_config


assert os.getenv("ENV", "test") == "test"


def test_gen_text(game_run, generated_text):
    config = load_game_config(game_run)
    # with open("test/fixtures/full_game_config2.json", "w") as f:
    #    json.dump(config, f, indent=4)
    with open("test/fixtures/full_game_config.json") as f:
        loaded_config = json.load(f)
    assert config == loaded_config
