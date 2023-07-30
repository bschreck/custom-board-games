from redis import Redis
from redis.exceptions import ResponseError
import os


def redis():
    return Redis(host=os.getenv("REDIS_HOST", 'localhost'), port=os.getenv("REDIS_PORT", "6379"), db=0)


def ensure_redis_game_run_exists(game_run):
    r = redis()
    if game_run not in r.json().get("game_runs", "."):
        r.json().set("game_runs", ".", {game_run: {}})


def ensure_redis_key_exists(game_run, key):
    r = redis()
    ensure_redis_game_run_exists(game_run)
    if key not in r.json().get("game_runs", f".{game_run}"):
        r.json().set("game_runs", f".{game_run}.key", {})


def save_game_config(game_run, config):
    ensure_redis_key_exists(game_run, "config")
    r = redis()
    # TODO: use when available
    # return r.json().merge('game_runs', f'.{game_run}.config', config)
    existing_config = load_game_config(game_run)
    res = r.json().set("game_runs", f".{game_run}.config", {**existing_config, **config})
    if not res:
        raise ValueError("Could not save game config")



def load_game_config(game_run):
    r = redis()
    try:
        return r.json().get("game_runs", f".{game_run}.config")
    except ResponseError:
        return {}