import json
from PIL import Image
import os
from custom_board_games.utils.redis import load_game_config
from conftest import INITIAL_IMAGE_DIM


assert os.getenv("ENV", "test") == "test"


def test_gen_images(game_run, generated_images):
    config = load_game_config(game_run)
    for _, image_config in config["images_by_name"].items():
        for path in image_config["image_paths"]:
            img = Image.open(path)
            assert max(img.size) == INITIAL_IMAGE_DIM
    # TODO: why is random not fully working, e.g. for color hex
    # with open("test/fixtures/full_game_config_with_images.json", "w") as f:
    #     json.dump(config, f, indent=4)
    with open("test/fixtures/full_game_config_with_images.json") as f:
        loaded_config = json.load(f)
    assert config == loaded_config


def test_scale_images(game_run, scaled_images):
    config = load_game_config(game_run)
    with open("test/fixtures/full_game_config_with_scaled_images.json", "w") as f:
        json.dump(config, f, indent=4)
    with open("test/fixtures/full_game_config_with_scaled_images.json") as f:
        loaded_config = json.load(f)
    assert config == loaded_config
    for _, image_config in config["images_by_name"].items():
        for path in image_config["image_paths"]:
            img = Image.open(path)
            # TODO: check the size against what's in config
            # for size_type, desired_size in prompt["sizes"].items():
            # assert max(img.size) == INITIAL_IMAGE_DIM
            # also for composites scaled below


def test_gen_composites(game_run, generated_images):
    config = load_game_config(game_run)
    with open("test/fixtures/full_game_config_with_composites.json", "w") as f:
        json.dump(config, f, indent=4)
    with open("test/fixtures/full_game_config_with_composites.json") as f:
        loaded_config = json.load(f)
    assert config == loaded_config


def test_gen_composites_scaled(game_run, scaled_images):
    config = load_game_config(game_run)
    with open("test/fixtures/full_game_config_with_composites_scaled.json", "w") as f:
        json.dump(config, f, indent=4)
    # with open('test/fixtures/full_game_config_with_composites.json') as f:
    #    loaded_config = json.load(f)
    # assert config == loaded_config
