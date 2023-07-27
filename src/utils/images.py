from PIL import Image, ImageDraw, ImageFont
from torchvision.transforms import GaussianBlur
import numpy as np


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

