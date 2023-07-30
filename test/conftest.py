from custom_board_games.utils.redis import redis
import pytest

@pytest.fixture
def game_run():
    return "35d3f929-fcc9-40db-b56d-a0cd743050aa"

@pytest.fixture
def cleared_game_run(game_run):
    redis().json().delete("game_runs", f".{game_run}")
    return game_run