from PIL import Image, ImageDraw, ImageFont
from stability_sdk import client
from torchvision.transforms import GaussianBlur
import io
from PIL import Image
import warnings
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
import numpy as np
import os


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
