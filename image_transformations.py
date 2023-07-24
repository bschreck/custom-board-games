import sys
import os
import io
import warnings

from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from PIL import Image, ImageDraw, ImageFont
from torchvision.transforms import GaussianBlur
import numpy as np
from dotenv import load_dotenv
load_dotenv()

# Our Host URL should not be prepended with "https" nor should it have a trailing slash.
os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'

stability_api = client.StabilityInference(
    key=os.environ['STABILITY_KEY'], # API Key reference.
    verbose=True, # Print debug messages.
    engine="stable-diffusion-xl-1024-v0-9", # Set the engine to use for generation.
    # Available engines: stable-diffusion-xl-1024-v0-9 stable-diffusion-v1 stable-diffusion-v1-5 stable-diffusion-512-v2-0 stable-diffusion-768-v2-0
    # stable-diffusion-512-v2-1 stable-diffusion-768-v2-1 stable-diffusion-xl-beta-v2-2-2 stable-inpainting-v1-0 stable-inpainting-512-v2-0
)

# https://medium.com/the-research-nest/how-to-create-fancy-artistic-text-effects-using-stable-diffusion-1857169f8c5d

def process_card_image(char_image_f, text_image_f, out_f):
    with Image.open(char_image_f) as char_image:
        print(char_image_f, char_image.format, f"{char_image.size}x{char_image.mode}")
        with Image.open(text_image_f) as text_image:
            print(char_image, text_image.format, f"{text_image.size}x{text_image.mode}")
            box = (100, 100, 400, 400)
            region = text_image.crop(box)
            region = region.transpose(Image.Transpose.ROTATE_180)
            char_image.paste(region, box)
        char_image.save(out_f)
        


# Returns a PIL image of text in black at the center of a 512*512 white background
# Note: Fontsize need to be changed for words, letters of different length
# # Single letters, font_size = 500, 5 letter words, font_size = 150
def create_text(text, font_size):
    font = ImageFont.truetype("fonts/arialbd.ttf", font_size)

    # Create a new image with a white background
    image = Image.new("RGB", (512, 512), (255, 255, 255))

    # Get the size of the text and calculate its position in the center of the image
    text_size = font.getbbox(text)
    text_x = (image.width - text_size[2]) / 2
    text_y = (image.height - text_size[3]) / 2

    # A method to create thicker text on the image
    # Define the number of shadow layers to create and the offset distance
    num_layers = 5
    offset = 2

    # Draw the text onto the image multiple times with a slight offset to create a shadow effect
    draw = ImageDraw.Draw(image)
    for i in range(num_layers):
        x = text_x + (i * offset)
        y = text_y + (i * offset)
        draw.text((x, y), text, font=font, fill=(0, 0, 0))

    # Draw the final text layer on top of the shadows
    draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0))

    return image
            
# Returns a PIL image of the mask of the given image
# param = "letter" masks the letters to inpaint
# paraam = "background" masks the background
def create_mask(image, letter_is_white=True, blur=False):
    # Convert the image to grayscale
    gray_image = image.convert('L')

    # Convert the grayscale image to a numpy array
    gray_array = np.array(gray_image)

    # Threshold the array to create a binary mask
    threshold = 128

    # letter -> letter is painted white
    # background -> background is painted white
    # All the white area is used for inpainting
    if letter_is_white:
        mask_array = np.where(gray_array > threshold, 0, 255).astype(np.uint8)
    else:
        mask_array = np.where(gray_array > threshold, 255, 0).astype(np.uint8)
    
    # Convert the mask array back to a PIL image
    mask_image = Image.fromarray(mask_array)

    if blur:
        blur = GaussianBlur(11,20)
        # im2 = im1.filter(ImageFilter.GaussianBlur(radius = 5))
        mask_image = blur(mask_image)

    return mask_image

def gen_stability_image_from_text(prompt, img, mask, dirname):
    answers = stability_api.generate(
        prompt=prompt,
        init_image=img,
        mask_image=mask,
        start_schedule=1,
        #seed=44332211, # If attempting to transform an image that was previously generated with our API,
        #                # initial images benefit from having their own distinct seed rather than using the seed of the original image generation.
        steps=50, # Amount of inference steps performed on image generation. Defaults to 30.
        cfg_scale=8.0, # Influences how strongly your generation is guided to match your prompt.
                       # Setting this value higher increases the strength in which it tries to match your prompt.
                       # Defaults to 7.0 if not specified.
        width=1024, # Generation width, if not included defaults to 512 or 1024 depending on the engine.
        height=1024, # Generation height, if not included defaults to 512 or 1024 depending on the engine.
        sampler=generation.SAMPLER_K_DPMPP_2M # Choose which sampler we want to denoise our generation with.
                                                     # Defaults to k_lms if not specified. Clip Guidance only supports ancestral samplers.
                                                     # (Available Samplers: ddim, plms, k_euler, k_euler_ancestral, k_heun, k_dpm_2, k_dpm_2_ancestral, k_dpmpp_2s_ancestral, k_lms, k_dpmpp_2m, k_dpmpp_sde)
    )

    # Set up our warning to print to the console if the adult content classifier is tripped.
    # If adult content classifier is not tripped, save generated image.
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
                answer.save(os.path.join(dirname, str(artifact.seed)+ ".png"))
                
if __name__ == '__main__':
    # process_card_image(sys.argv[1], sys.argv[2], sys.argv[3])
    prompt_1 = "Colorful rainbow paints splashed around"
    prompt_2 = "A beautiful and calm sky scenery"

    letters = create_text("HELLO", 150)
    bg_mask = create_mask(letters, letter_is_white=False, blur=False)
    letter_mask = create_mask(letters, letter_is_white=True, blur=False)
    os.makedirs("output_letter", exist_ok=True)
    letter_out = gen_stability_image_from_text(prompt=prompt_1, img=letters, mask=letter_mask, dirname="output_letter")
    os.makedirs("output_bg", exist_ok=True)
    bg_out = gen_stability_image_from_text(prompt=prompt_2, img=letter_out, mask=bg_mask, dirname="output_bg")

    # TO ChatGPT:
""" 
Suggest a Google font, available via permalink, to use for the title that evokes the style, story, imagery you created.
This font will be embedded into the standard Google fonts link, so your output needs a single word.
For instance, for the font "Open Sans", the permalink is `https://fonts.google.com/specimen/Open+Sans`, so your
output should be `Open+Sans`
"""