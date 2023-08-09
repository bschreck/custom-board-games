import os
import shutil
import concurrent.futures
from pathlib import Path

from .utils.redis import save_game_config, load_game_config
from .utils.mock_stable_diffusion import (
    gen_stability_image_from_text as mock_gen_stability_image_from_text,
    mock_gen_upscaled_image as mock_gen_upscaled_image,
)
from .utils.images import (
    gen_stability_image_from_text as real_gen_stability_image_from_text,
    gen_upscaled_image as real_gen_upscaled_image,
)
from .config import GENERATED_IMAGE_DIR
import fire

if os.getenv("ENV", "test") == "test":
    gen_stability_image_from_text = mock_gen_stability_image_from_text
    gen_upscaled_image = mock_gen_upscaled_image
else:
    gen_stability_image_from_text = real_gen_stability_image_from_text
    gen_upscaled_image = real_gen_upscaled_image


def add_nested_key_to_dict(d, key, value):
    keys = key.split(".")
    for key in keys[:-1]:
        if key not in d:
            d[key] = {}
        d = d[key]
    d[keys[-1]] = value


def get_imgs_by_name():
    config = load_game_config("test_game_run")
    return list(config["images_by_name"].keys())


IMAGE_PROMPTS_KEY = "image_prompts"
IMAGES_BY_NAME_KEY = "images_by_name"
IMAGE_PROMPTS_KEY_SCALED = "image_prompts_scaled"
IMAGES_BY_NAME_KEY_SCALED = "images_by_name_scaled"


def save_image_mapping(game_run, prompt_id, image_paths, save_top_level_name=True, scaled=False):
    config = load_game_config(game_run)
    image_prompts_key = IMAGE_PROMPTS_KEY_SCALED if scaled else IMAGE_PROMPTS_KEY
    images_by_name_key = IMAGES_BY_NAME_KEY_SCALED if scaled else IMAGES_BY_NAME_KEY
    if image_prompts_key not in config:
        config[image_prompts_key] = {}
    if images_by_name_key not in config:
        config[images_by_name_key] = {}
    if prompt_id not in config[image_prompts_key]:
        config[image_prompts_key][prompt_id] = {}
    config[image_prompts_key][prompt_id]["image_paths"] = image_paths
    # TODO: top level name is now irrelevant/extra info since we have prompt_id as a key
    # but the other place they are stored is "image_prompts", which the component
    # images shouldn't be saved under unless that key is changed
    if save_top_level_name:
        add_nested_key_to_dict(
            config,
            f"{images_by_name_key}.{prompt_id}",
            {"composite": False, "source_images": [prompt_id], "image_paths": image_paths},
        )
    save_game_config(game_run, config)


def image_prompt_dicts_by_type(type, game_run, scaled=False):
    config = load_game_config(game_run)
    prompts = {
        prompt_id: prompt_config
        for prompt_id, prompt_config in config[IMAGE_PROMPTS_KEY].items()
        if type in prompt_config["types"]
    }
    if scaled:
        prompts = {
            prompt_id: {**prompt_config, **config[IMAGE_PROMPTS_KEY_SCALED][prompt_id]}
            for prompt_id, prompt_config in prompts.items()
        }
    return prompts


def combine_images(component_image_paths, save_path):
    shutil.copyfile(component_image_paths[0], save_path)
    # raise ValueError("not implemented")


def combine_char_logo_images(char_img_path, logo_img_path, save_path):
    # TODO actually implement
    # raise ValueError("not implemented")
    shutil.copyfile(char_img_path, save_path)


def gen_component_overview_image(game_run, scaled=False):
    # TODO: what scale should this be and where should we define that?
    images_by_name_key = IMAGES_BY_NAME_KEY_SCALED if scaled else IMAGES_BY_NAME_KEY
    config = load_game_config(game_run)
    component_images = image_prompt_dicts_by_type("component", game_run, scaled=scaled)
    save_path = Path(GENERATED_IMAGE_DIR) / game_run / "components_overview.png"
    combine_images([c["image_paths"][0] for c in component_images.values()], save_path)
    # TODO: this will overwrite later,
    # and fail if doesn't exist
    # needs to match to the variants in config
    add_nested_key_to_dict(
        config,
        f"{images_by_name_key}.components_overview_image",
        {"image_paths": [str(save_path)], "source_images": list(component_images.keys()), "composite": True},
    )
    save_game_config(game_run, config)


def gen_setup_image(game_run, scaled=False):
    # TODO: what scale should this be and where should we define that?
    # TODO actually implement
    images_by_name_key = IMAGES_BY_NAME_KEY_SCALED if scaled else IMAGES_BY_NAME_KEY
    config = load_game_config(game_run)
    component_images = image_prompt_dicts_by_type("component", game_run, scaled=scaled)
    save_path = Path(GENERATED_IMAGE_DIR) / game_run / "setup.png"
    shutil.copyfile(component_images["token_image"]["image_paths"][0], save_path)

    add_nested_key_to_dict(
        config,
        f"{images_by_name_key}.setup_image",
        {"image_paths": [str(save_path)], "source_images": list(component_images.keys()), "composite": True},
    )
    save_game_config(game_run, config)


def gen_character_images(game_run, scaled=False):
    # TODO: what scale should this be and where should we define that?
    images_by_name_key = IMAGES_BY_NAME_KEY_SCALED if scaled else IMAGES_BY_NAME_KEY
    config = load_game_config(game_run)
    char_images = image_prompt_dicts_by_type("character_image", game_run, scaled=scaled)
    logo_images = image_prompt_dicts_by_type("character_image_logo", game_run, scaled=scaled)
    for prompt_id, char_img in char_images.items():
        name = f"{prompt_id}_with_logo"
        logo_prompt_id = prompt_id.replace("_image", "_logo")
        logo_img = logo_images[logo_prompt_id]
        save_path = Path(GENERATED_IMAGE_DIR) / game_run / name
        combine_char_logo_images(char_img["image_paths"][0], logo_img["image_paths"][0], save_path)
        # TODO: this will overwrite later,
        # and fail if doesn't exist

        add_nested_key_to_dict(
            config,
            f"{images_by_name_key}.{name}",
            {"image_paths": [str(save_path)], "source_images": [prompt_id, logo_prompt_id], "composite": True},
        )
        save_game_config(game_run, config)


def gen_images_from_game_run(game_run, max_dim=128, nthreads=None, verbose=True):
    output_dirname = os.path.join(GENERATED_IMAGE_DIR, game_run)
    os.makedirs(output_dirname, exist_ok=True)
    config = load_game_config(game_run)

    def gen_image(prompt, prompt_id):
        saved_image_paths = []
        for size_type, desired_size in prompt["sizes"].items():
            dw, dh = desired_size
            if dw > dh:
                w = max_dim
                h = int((dh / dw) * max_dim)
            else:
                h = max_dim
                w = int((dw / dh) * max_dim)

            try:
                saved_image_paths.extend(
                    gen_stability_image_from_text(
                        prompt=prompt["prompt"],
                        width=w,
                        height=h,
                        samples=1,
                        dirname=Path(output_dirname) / prompt_id / size_type,
                    )
                )
            except Exception as e:
                import pdb

                pdb.set_trace()

        # TODO maybe one more nesting here in the config because I nest by size_type too
        try:
            save_image_mapping(game_run, prompt_id, saved_image_paths)
        except Exception as e:
            import pdb

            pdb.set_trace()

    if nthreads is None:
        nthreads = len(config["image_prompts"])
    with concurrent.futures.ThreadPoolExecutor(max_workers=nthreads) as executor:
        future_to_prompt = {
            executor.submit(gen_image, prompt, prompt_id): prompt
            for prompt_id, prompt in config["image_prompts"].items()
        }
        failed_prompts = []
        for future in concurrent.futures.as_completed(future_to_prompt):
            prompt = future_to_prompt[future]
            try:
                future.result()
            except Exception as exc:
                print("%r generated an exception: %s" % (prompt, exc))
                failed_prompts.append(prompt)

    if len(failed_prompts):
        # TODO: perhaps allow some to fail and retry
        raise RuntimeError("Failed to generate images:", failed_prompts)


def gen_composite_images_from_game_run(game_run, scaled=False, nthreads=None, verbose=False):
    output_dirname = os.path.join(GENERATED_IMAGE_DIR, game_run)
    os.makedirs(output_dirname, exist_ok=True)
    gen_component_overview_image(game_run, scaled=scaled)
    gen_setup_image(game_run, scaled=scaled)
    gen_character_images(game_run, scaled=scaled)


def scale_images_from_game_run(game_run, nthreads=None, verbose=True):
    config = load_game_config(game_run)
    output_dirname = Path(GENERATED_IMAGE_DIR) / game_run / "scaled"
    os.makedirs(output_dirname, exist_ok=True)

    def upscale_image(prompt, prompt_id):
        image_paths = []
        for size_type, desired_size in prompt["sizes"].items():
            image_paths.extend(
                gen_upscaled_image(
                    input_image_path=prompt["image_paths"][0],
                    original_prompt=prompt["prompt"],
                    new_width=desired_size[0],
                    output_dirname=output_dirname / prompt_id / size_type,
                    verbose=verbose,
                )
            )
        # TODO maybe one more nesting here in the config because I nest by size_type too
        save_image_mapping(game_run, prompt_id, image_paths, scaled=True)

    if nthreads is None:
        nthreads = len(config["image_prompts"])
    with concurrent.futures.ThreadPoolExecutor(max_workers=nthreads) as executor:
        future_to_prompt = {
            executor.submit(upscale_image, prompt, prompt_id): prompt
            for prompt_id, prompt in config["image_prompts"].items()
        }
        for future in concurrent.futures.as_completed(future_to_prompt):
            prompt = future_to_prompt[future]
            try:
                future.result()
            except Exception as exc:
                print("%r generated an exception: %s" % (prompt, exc))
                raise


def main(game_run=None, scale=False, gen_composite=False, nthreads=None, verbose=True):
    gen_images_from_game_run(game_run, nthreads=nthreads, verbose=verbose)
    if scale:
        scale_images_from_game_run(game_run, nthreads=nthreads, verbose=verbose)
    if gen_composite:
        gen_composite_images_from_game_run(game_run, scaled=scale, nthreads=nthreads, verbose=verbose)


if __name__ == "__main__":
    fire.Fire(main)

    # bg_out = gen_stability_image_from_text(name="bg", prompt=prompt_2, dirname="output_bg", img=letter_out, mask=bg_mask)

    ## process_card_image(sys.argv[1], sys.argv[2], sys.argv[3])
    # prompt_1 = "Colorful rainbow paints splashed around"
    # prompt_2 = "A beautiful and calm sky scenery"

    # letters = create_text("HELLO", 150)
    # bg_mask = create_mask(letters, letter_is_white=False, blur=False)
    # letter_mask = create_mask(letters, letter_is_white=True, blur=False)
    # os.makedirs("output_letter", exist_ok=True)
    # letter_out = gen_stability_image_from_text(prompt=prompt_1, dirname="output_letter", img=letters, mask=letter_mask)
    # os.makedirs("output_bg", exist_ok=True)
    # bg_out = gen_stability_image_from_text(prompt=prompt_2, dirname="output_bg", img=letter_out, mask=bg_mask)
