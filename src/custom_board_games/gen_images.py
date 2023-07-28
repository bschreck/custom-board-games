import sys
import os
import io
import warnings
import yaml
import concurrent.futures

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from PIL import Image
from config import GENERATED_IMAGE_DIR, GENERATED_OUTPUT_STYLE_DIR, GENERATED_OUTPUT_CONFIG_DIR


# https://medium.com/the-research-nest/how-to-create-fancy-artistic-text-effects-using-stable-diffusion-1857169f8c5d


def gen_stability_image_from_text(prompt, name, dirname, samples=1, width=512, height=512, img=None, mask=None):
    os.makedirs(os.path.join(dirname, name), exist_ok=True)
    stability_api = client.StabilityInference(
        key=os.environ['STABILITY_KEY'], # API Key reference.
        verbose=True, # Print debug messages.
        enginer="stable-diffusion-512-v2-1"
        # engine="stable-diffusion-xl-1024-v0-9", # Set the engine to use for generation.
        # Available engines: stable-diffusion-xl-1024-v0-9 stable-diffusion-v1 stable-diffusion-v1-5 stable-diffusion-512-v2-0 stable-diffusion-768-v2-0
        # stable-diffusion-512-v2-1 stable-diffusion-768-v2-1 stable-diffusion-xl-beta-v2-2-2 stable-inpainting-v1-0 stable-inpainting-512-v2-0
    )
    answers = stability_api.generate(
        prompt=prompt,
        init_image=img,
        mask_image=mask,
        start_schedule=1,
        samples=samples,
        #seed=44332211, # If attempting to transform an image that was previously generated with our API,
        #                # initial images benefit from having their own distinct seed rather than using the seed of the original image generation.
        steps=30, # Amount of inference steps performed on image generation. Defaults to 30.
        cfg_scale=8.0, # Influences how strongly your generation is guided to match your prompt.
                       # Setting this value higher increases the strength in which it tries to match your prompt.
                       # Defaults to 7.0 if not specified.
        width=width, # Generation width, if not included defaults to 512 or 1024 depending on the engine.
        height=height, # Generation height, if not included defaults to 512 or 1024 depending on the engine.
        sampler=generation.SAMPLER_K_DPMPP_2M # Choose which sampler we want to denoise our generation with.
                                                     # Defaults to k_lms if not specified. Clip Guidance only supports ancestral samplers.
                                                     # (Available Samplers: ddim, plms, k_euler, k_euler_ancestral, k_heun, k_dpm_2, k_dpm_2_ancestral, k_dpmpp_2s_ancestral, k_lms, k_dpmpp_2m, k_dpmpp_sde)
    )

    # Set up our warning to print to the console if the adult content classifier is tripped.
    # If adult content classifier is not tripped, save generated image.
    paths = []
    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                warnings.warn(
                    "Your request activated the API's safety filters and could not be processed."
                    "Please modify the prompt and try again.")
            if artifact.type == generation.ARTIFACT_IMAGE:
                # TODO: get rid of global
                global answer
                answer = Image.open(io.BytesIO(artifact.binary))
                path = os.path.join(dirname, name, str(artifact.seed)+ ".png")
                answer.save(path)
                paths.append(path)
    return paths
                

def save_image_mapping(game_run, prompt_idx, image_paths, save_top_level_name=True):
    config = open_art_text_file(game_run)
    config["image_prompts"][prompt_idx]["image_paths"] = image_paths
    if save_top_level_name:
        config[config["image_prompts"][prompt_idx]["name"]] = image_paths
    save_art_text_file(game_run, config)

def open_art_text_file(game_run):
    generated_art_text_file = os.path.join(GENERATED_OUTPUT_STYLE_DIR, game_run, 'art_text.yaml')
    with open(generated_art_text_file) as f:
        config = yaml.load(f, Loader=Loader)
    return config

def write_art_text_file(game_run, to_write):
    generated_art_text_file = os.path.join(GENERATED_OUTPUT_STYLE_DIR, game_run, 'art_text.yaml')
    with open(generated_art_text_file, 'w') as f:
        yaml.dump(to_write, f, Dumper=Dumper)

def save_art_text_file(game_run, new_entries):
    # TODO: make into a context
    art_text = open_art_text_file(game_run)
    art_text.update(new_entries)
    write_art_text_file(game_run, art_text)
    
def image_paths_by_type(type, game_run):
    config = open_art_text_file(game_run)
    return [
        prompt_config
        for prompt_config
        in config["image_prompts"]
        if "component" in prompt_config["types"]]

def combine_images(component_image_paths, save_path):
    # TODO
    raise ValueError("not implemented")

def combine_char_logo_images(char_img_path, logo_img_path, save_path):
    # TODO
    raise ValueError("not implemented")

def gen_component_overview_image(game_run):
    config = open_art_text_file(game_run)
    component_images = image_paths_by_type('component', game_run)
    save_path = os.path.join(GENERATED_IMAGE_DIR, game_run, "component_overview.png")
    combine_images([c["path"] for c in component_images], save_path)
    # TODO: this will overwrite later,
    # and fail if doesn't exist
    # needs to match to the variants in config
    config["images"]["component_overview_image"] = {"src": save_path}
    save_art_text_file(game_run, config)

def gen_setup_image(game_run):
    pass

def gen_character_images(game_run):
    config = open_art_text_file(game_run)
    char_images = image_paths_by_type('character_image', game_run)
    logo_images = image_paths_by_type('character_image_logo', game_run)
    for char_img, logo_img in zip(char_images, logo_images):
        name = char_img["name"] + "_with_logo"
        save_path = os.path.join(GENERATED_IMAGE_DIR, game_run, name)
        combine_char_logo_images(char_img["path"], logo_img["path"], save_path)
        # TODO: this will overwrite later,
        # and fail if doesn't exist
        config["images"][name]["src"] = save_path
        save_art_text_file(config)
    
def gen_images_from_config_file(game_run):
    output_dirname = os.path.join(GENERATED_IMAGE_DIR, game_run)
    config = open_art_text_file(game_run)

    def gen_image(prompt, prompt_idx):
        saved_image_paths = gen_stability_image_from_text(
            name=prompt['name'], 
            prompt=prompt['prompt'], 
            samples=1,
            dirname=os.path.join(output_dirname, prompt['type'])
        )
        save_image_mapping(game_run, prompt_idx, saved_image_paths)

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(config['image_prompts'])) as executor:
        future_to_prompt = {executor.submit(gen_image, prompt, i): prompt for i, prompt in enumerate(config['image_prompts'])}
        for future in concurrent.futures.as_completed(future_to_prompt):
            prompt = future_to_prompt[future]
            try:
                future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (prompt, exc))

    gen_component_overview_image(game_run)
    gen_setup_image(game_run)
    gen_character_images(game_run)


if __name__ == '__main__':
    game_run = sys.argv[1]
    gen_images_from_config_file(game_run, verbose=True)



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
