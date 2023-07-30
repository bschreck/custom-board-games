import json
import fire
import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


def yaml_to_json(in_yaml, out_json):
    with open(in_yaml) as f:
        config = yaml.load(f, Loader=Loader)

    with open(out_json, "w") as f:
        json.dump(config, f, indent=4)


if __name__ == "__main__":
    fire.Fire(yaml_to_json)
