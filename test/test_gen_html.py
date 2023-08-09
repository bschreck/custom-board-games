import json
from PIL import Image
from bs4 import BeautifulSoup
import os
from custom_board_games.utils.redis import load_game_config


assert os.getenv("ENV", "test") == "test"


def test_gen_html(cleared_game_run, generated_html):
    config = load_game_config(cleared_game_run)
    with open("test/fixtures/full_game_config_with_html2.json", "w") as f:
        json.dump(config, f)
    # with open('test/fixtures/full_game_config_with_html.json') as f:
    #    loaded_config = json.load(f)
    # assert config == loaded_config
    with open(config["rendered_html"]) as f:
        soup = BeautifulSoup(f, "html.parser")
    image_tags = soup.find_all("img")
    for tag in image_tags:
        path = tag.attrs["src"]
        img = Image.open(path)
        print(img.size)
