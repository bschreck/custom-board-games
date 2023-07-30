import json
import os
from custom_board_games.gen_text import main
from custom_board_games.gen_images import gen_images_from_game_run
from custom_board_games.utils.redis import load_game_config


assert os.getenv("ENV", "test") == "test"


def test_gen_images(cleared_game_run):
    #with open('test/fixtures/full_game_config_with_images.json') as f:
    #    loaded_config = json.load(f)
    game_run = "35d3f929-fcc9-40db-b56d-a0cd743050aa"
    main("coup", "Angry Birds", game_run=cleared_game_run)
    gen_images_from_game_run(cleared_game_run, nthreads=1)
    config = load_game_config(cleared_game_run)
    with open('test/fixtures/full_game_config_with_images.json', 'w') as f:
        json.dump(config, f, indent=4)
    #assert config == loaded_config

