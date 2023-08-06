from redis import Redis
from redis.exceptions import ResponseError
import os


def redis():
    return Redis(host=os.getenv("REDIS_HOST", "localhost"), port=os.getenv("REDIS_PORT", "6379"), db=0)


def ensure_redis_game_run_exists(game_run):
    r = redis()
    game_runs_top_level = r.json().get("game_runs", ".")
    if not game_runs_top_level or game_run not in game_runs_top_level:
        r.json().set("game_runs", ".", {game_run: {}})


def ensure_redis_key_exists(game_run, key):
    r = redis()
    ensure_redis_game_run_exists(game_run)
    existing_game_run_config = r.json().get("game_runs", f".{game_run}")
    if not existing_game_run_config or key not in existing_game_run_config:
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


def expand_key_components(key_parts, value):
    expanded = {key_parts[-1]: value}
    key_parts = key_parts[:-1]
    for k in key_parts[::-1]:
        expanded = {k: expanded}
    return expanded


def save_nested_key_to_game_config(game_run, key, value):
    ensure_redis_key_exists(game_run, "config")
    r = redis()
    top_level_existing_config = load_game_config(game_run)
    existing_config = top_level_existing_config
    key_parts = key.split(".")
    set_key = f".{game_run}.config.{key_parts[0]}"
    new_config = expand_key_components(key_parts[1:], value)
    for k in key_parts[1:-1]:
        if k in existing_config:
            set_key += f".{k}"
            new_config = new_config[k]
        else:
            break

    res = r.json().set("game_runs", set_key, new_config)
    if not res:
        raise ValueError("Could not save game config")


def load_game_config(game_run):
    r = redis()
    try:
        return r.json().get("game_runs", f".{game_run}.config")
    except ResponseError:
        return {}


def load_key_from_game_config(game_run, key):
    r = redis()
    return r.json().get("game_runs", f".{game_run}.config.{key}")
