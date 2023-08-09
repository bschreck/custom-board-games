import json
from pathlib import Path
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

    for prompt_id, image_config in config["images_by_name_scaled"].items():
        for path in image_config["image_paths"]:
            img = Image.open(path)
            for size_type, desired_size in config["image_prompts"][prompt_id]["sizes"].values():
                if Path(path).parent.name == size_type:
                    assert img.size == desired_size


def test_gen_composites(game_run, generated_composite_images):
    config = load_game_config(game_run)
    with open("test/fixtures/full_game_config_with_composites.json", "w") as f:
        json.dump(config, f, indent=4)
    with open("test/fixtures/full_game_config_with_composites.json") as f:
        loaded_config = json.load(f)
    assert config == loaded_config
    assert_all_component_images(config, "images_by_name")


def test_gen_composites_scaled(game_run, generated_composite_images_scaled):
    config = load_game_config(game_run)
    with open("test/fixtures/full_game_config_with_composites_scaled.json", "w") as f:
        json.dump(config, f, indent=4)
    assert "components_overview_image" in config["images_by_name_scaled"]
    assert "setup_image" in config["images_by_name_scaled"]
    assert all(
        f"{char}_image_with_logo" in config["images_by_name_scaled"]
        for char in ["Duke", "Ambassador", "Captain", "Contessa", "Assassin"]
    )
    # with open('test/fixtures/full_game_config_with_composites.json') as f:
    #    loaded_config = json.load(f)
    # assert config == loaded_config
    assert_all_component_images(config, "images_by_name_scaled")
    # TODO: we don't actually know what size these will be
    # for prompt_id, image_config in config["images_by_name_scaled"].items():
    #    for path in image_config["image_paths"]:
    #        img = Image.open(path)
    #        for size_type, desired_size in config["image_prompts"][prompt_id]["sizes"].values():
    #            if Path(path).parent.name == size_type:
    #                assert img.size == desired_size


def assert_all_component_images(config, images_by_name_key):
    assert "components_overview_image" in config[images_by_name_key]
    assert config[images_by_name_key]["components_overview_image"]["composite"]
    assert config[images_by_name_key]["components_overview_image"]["source_images"] == [
        "token_image",
        "Duke_image",
        "Duke_logo",
        "Assassin_image",
        "Assassin_logo",
        "Captain_image",
        "Captain_logo",
        "Ambassador_image",
        "Ambassador_logo",
        "Contessa_image",
        "Contessa_logo",
    ]
    path = config[images_by_name_key]["components_overview_image"]["image_paths"][0]
    Image.open(path)

    assert "setup_image" in config[images_by_name_key]
    assert config[images_by_name_key]["setup_image"]["composite"]
    assert config[images_by_name_key]["setup_image"]["source_images"] == [
        "token_image",
        "Duke_image",
        "Duke_logo",
        "Assassin_image",
        "Assassin_logo",
        "Captain_image",
        "Captain_logo",
        "Ambassador_image",
        "Ambassador_logo",
        "Contessa_image",
        "Contessa_logo",
    ]
    path = config[images_by_name_key]["setup_image"]["image_paths"][0]
    Image.open(path)

    for char in ["Duke", "Ambassador", "Captain", "Contessa", "Assassin"]:
        image_name = f"{char}_image_with_logo"
        assert image_name in config[images_by_name_key]
        assert config[images_by_name_key][image_name]["composite"]
        assert config[images_by_name_key][image_name]["source_images"] == [f"{char}_image", f"{char}_logo"]
        path = config[images_by_name_key][image_name]["image_paths"][0]
        Image.open(path)
