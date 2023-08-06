import json
import os
from custom_board_games.utils.redis import load_game_config


assert os.getenv("ENV", "test") == "test"


def test_gen_html(game_run, generated_html):
    config = load_game_config(cleared_game_run)
    with open("test/fixtures/full_game_config_with_html2.json", "w") as f:
        json.dump(config, f)
    # with open('test/fixtures/full_game_config_with_html.json') as f:
    #    loaded_config = json.load(f)
    # assert config == loaded_config
