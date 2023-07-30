import sys
import os
import concurrent.futures

from .utils.redis import redis, save_game_config, load_game_config, ensure_redis_key_exists
from .utils.mock_stable_diffusion import gen_stability_image_from_text as mock_gen_stability_image_from_text
from .utils.images import gen_stability_image_from_text as real_gen_stability_image_from_text
from .config import GENERATED_IMAGE_DIR

if os.getenv('ENV', "test") == "test":
    gen_stability_image_from_text = mock_gen_stability_image_from_text
else:
    gen_stability_image_from_text = real_gen_stability_image_from_text

def save_image_mapping(game_run, prompt_idx, image_paths, save_top_level_name=True):
    config = load_game_config(game_run)
    config["image_prompts"][prompt_idx]["image_paths"] = image_paths
    if save_top_level_name:
        config[config["image_prompts"][prompt_idx]["name"]] = image_paths
    save_game_config(game_run, config)

def image_paths_by_type(type, game_run):
    config = load_game_config(game_run)
    return [
        prompt_config
        for prompt_config
        in config["image_prompts"]
        if type in prompt_config["types"]]

def combine_images(component_image_paths, save_path):
    # TODO
    raise ValueError("not implemented")

def combine_char_logo_images(char_img_path, logo_img_path, save_path):
    # TODO
    raise ValueError("not implemented")

def gen_component_overview_image(game_run):
    config = load_game_config(game_run)
    component_images = image_paths_by_type('component', game_run)
    save_path = os.path.join(GENERATED_IMAGE_DIR, game_run, "component_overview.png")
    combine_images([c["path"] for c in component_images], save_path)
    # TODO: this will overwrite later,
    # and fail if doesn't exist
    # needs to match to the variants in config
    config["images"]["component_overview_image"] = {"src": save_path}
    save_game_config(game_run, config)

def gen_setup_image(game_run):
    pass

def gen_character_images(game_run):
    config = load_game_config(game_run)
    char_images = image_paths_by_type('character_image', game_run)
    logo_images = image_paths_by_type('character_image_logo', game_run)
    for char_img, logo_img in zip(char_images, logo_images):
        name = char_img["name"] + "_with_logo"
        save_path = os.path.join(GENERATED_IMAGE_DIR, game_run, name)
        combine_char_logo_images(char_img["path"], logo_img["path"], save_path)
        # TODO: this will overwrite later,
        # and fail if doesn't exist
        config["images"][name]["src"] = save_path
        save_game_config(config)
    
def gen_images_from_game_run(game_run, nthreads=None, verbose=True):
    output_dirname = os.path.join(GENERATED_IMAGE_DIR, game_run)
    os.makedirs(output_dirname, exist_ok=True)
    config = load_game_config(game_run)

    def gen_image(prompt, prompt_idx):
        saved_image_paths = gen_stability_image_from_text(
            name=prompt['name'], 
            prompt=prompt['prompt'], 
            samples=1,
            dirname=output_dirname
        )
        save_image_mapping(game_run, prompt_idx, saved_image_paths)
    gen_image(config['image_prompts'][0], 0)
    if nthreads is None:
        nthreads = len(config['image_prompts'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=nthreads) as executor:
        future_to_prompt = {executor.submit(gen_image, prompt, i): prompt for i, prompt in enumerate(config['image_prompts'])}
        for future in concurrent.futures.as_completed(future_to_prompt):
            prompt = future_to_prompt[future]
            try:
                future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (prompt, exc))

    #gen_component_overview_image(game_run)
    #gen_setup_image(game_run)
    #gen_character_images(game_run)


if __name__ == '__main__':
    game_run = sys.argv[1]
    gen_images_from_game_run(game_run, verbose=True)



    # bg_out = gen_stability_image_from_text(name="bg", prompt=prompt_2, dirname="output_bg", img=letter_out, mask=bg_mask)

    ## process_card_image(sys.argv[1], sys.argv[2], sys.argv[3])
    #prompt_1 = "Colorful rainbow paints splashed around"
    #prompt_2 = "A beautiful and calm sky scenery"

    #letters = create_text("HELLO", 150)
    #bg_mask = create_mask(letters, letter_is_white=False, blur=False)
    #letter_mask = create_mask(letters, letter_is_white=True, blur=False)
    #os.makedirs("output_letter", exist_ok=True)
    #letter_out = gen_stability_image_from_text(prompt=prompt_1, dirname="output_letter", img=letters, mask=letter_mask)
    #os.makedirs("output_bg", exist_ok=True)
    #bg_out = gen_stability_image_from_text(prompt=prompt_2, dirname="output_bg", img=letter_out, mask=bg_mask)
