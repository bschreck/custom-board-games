from custom_board_games.utils.redis import redis
from custom_board_games.gen_text import gen_game_text
from custom_board_games.gen_images import (
    gen_images_from_game_run,
    scale_images_from_game_run,
    gen_composite_images_from_game_run,
)
from custom_board_games.gen_html import gen_html_from_game_run
import pytest
import numpy as np

rng = np.random.default_rng(2021)


INITIAL_IMAGE_DIM = 64


@pytest.fixture(scope="module")
def game_run():
    return "test_game_run"


@pytest.fixture(scope="module")
def cleared_game_run(game_run):
    redis().json().delete("game_runs", f".{game_run}")
    return game_run


@pytest.fixture(scope="module")
def generated_text(cleared_game_run):
    gen_game_text(cleared_game_run, "coup", "Angry Birds", verbose=False, rng=rng)


@pytest.fixture(scope="module")
def generated_images(cleared_game_run, generated_text):
    gen_images_from_game_run(cleared_game_run, max_dim=INITIAL_IMAGE_DIM, nthreads=1, verbose=False)


@pytest.fixture(scope="module")
def scaled_images(cleared_game_run, generated_images):
    scale_images_from_game_run(cleared_game_run, nthreads=1, verbose=False)


@pytest.fixture(scope="module")
def generated_composite_image(cleared_game_run, generated_images):
    gen_composite_images_from_game_run(game_run, scaled=False, nthreads=1, verbose=False)


@pytest.fixture(scope="module")
def generated_composite_image_scaled(cleared_game_run, scaled_images):
    gen_composite_images_from_game_run(game_run, scaled=True, nthreads=1, verbose=False)


@pytest.fixture(scope="module")
def generated_html(cleared_game_run, scaled_images):
    gen_html_from_game_run(cleared_game_run, "test/html_rendered/coup_angry_birds_test.html")
