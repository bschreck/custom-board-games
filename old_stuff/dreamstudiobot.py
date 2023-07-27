import os
import io
import warnings
from PIL import Image
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from dotenv import load_dotenv
load_dotenv()

# Our Host URL should not be prepended with "https" nor should it have a trailing slash.
os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'

# Sign up for an account at the following link to get an API Key.
# https://platform.stability.ai/

# Click on the following link once you have created an account to be taken to your API Key.
# https://platform.stability.ai/account

# Paste your API Key below.

# os.environ['STABILITY_KEY'] = 'key-goes-here'

stability_api = client.StabilityInference(
    key=os.environ['STABILITY_KEY'], # API Key reference.
    verbose=True, # Print debug messages.
    #engine="stable-diffusion-xl-1024-v0-9", # Set the engine to use for generation.
    engine="stable-diffusion-v1-5", # Set the engine to use for generation.
    # Available engines: stable-diffusion-xl-1024-v0-9 stable-diffusion-v1 stable-diffusion-v1-5 stable-diffusion-512-v2-0 stable-diffusion-768-v2-0
    # stable-diffusion-512-v2-1 stable-diffusion-768-v2-1 stable-diffusion-xl-beta-v2-2-2 stable-inpainting-v1-0 stable-inpainting-512-v2-0
)

NEGATIVE_PROMPT="ugly, tiling, poorly drawn hands, poorly drawn feet, poorly drawn face, out of frame, extra limbs, disfigured, deformed, body out of frame, bad anatomy, watermark, signature, cut off, low contrast, underexposed, overexposed, bad art, beginner, amateur, distorted face, blurry, draft, grainy"

def gen_images(prompt, dirname):
# Set up our initial generation parameters.
    answers = stability_api.generate(
        prompt=prompt,
        #seed=992446758, # If a seed is provided, the resulting generated image will be deterministic.
        #                # What this means is that as long as all generation parameters remain the same, you can always recall the same image simply by generating it again.
        #                # Note: This isn't quite the case for CLIP Guided generations, which we tackle in the CLIP Guidance documentation.
        steps=50, # Amount of inference steps performed on image generation. Defaults to 30.
        cfg_scale=8.0, # Influences how strongly your generation is guided to match your prompt.
                       # Setting this value higher increases the strength in which it tries to match your prompt.
                       # Defaults to 7.0 if not specified.
        width=1024, # Generation width, if not included defaults to 512 or 1024 depending on the engine.
        height=1024, # Generation height, if not included defaults to 512 or 1024 depending on the engine.
        samples=1, # Number of images to generate, defaults to 1 if not included.
        sampler=generation.SAMPLER_K_DPMPP_2M # Choose which sampler we want to denoise our generation with.
                                                     # Defaults to k_dpmpp_2m if not specified. Clip Guidance only supports ancestral samplers.
                                                     # (Available Samplers: ddim, plms, k_euler, k_euler_ancestral, k_heun, k_dpm_2, k_dpm_2_ancestral, k_dpmpp_2s_ancestral, k_lms, k_dpmpp_2m, k_dpmpp_sde)
    )

    # Set up our warning to print to the console if the adult content classifier is tripped.
    # If adult content classifier is not tripped, save generated images.
    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                warnings.warn(
                    "Your request activated the API's safety filters and could not be processed."
                    "Please modify the prompt and try again.")
            if artifact.type == generation.ARTIFACT_IMAGE:
                img = Image.open(io.BytesIO(artifact.binary))
                img.save(os.path.join(dirname, str(artifact.seed)+ ".png")) # Save our generated images with their seed number as the filename.


with open("prompts/phrase_output_1.txt") as f:
    captions = [
        l.replace("Image caption: ", "")
        for l in f.readlines()
        if l.lower().startswith("image caption:")
    ]

additional_keywords = ["Concept art", "art nouveau", "artstation", "unreal engine", "dramatic"]
for i, caption in enumerate(captions):
    dirname = f"caption{i}"
    os.makedirs(dirname, exist_ok=True)
    gen_images(caption + " " + " ".join(additional_keywords), dirname)