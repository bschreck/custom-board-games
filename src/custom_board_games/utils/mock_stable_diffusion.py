from PIL import Image
import numpy as np
import os
from threading import Lock
import contextlib


image_names = [f"{i}.png" for i in range(100)]
lock = Lock()
image_idx = [0]


@contextlib.contextmanager
def next_image_idx():
    lock.acquire(blocking=True, timeout=-1)
    try:
        yield image_idx[0]
        image_idx[0] += 1
    finally:
        lock.release()


def gen_stability_image_from_text(prompt, dirname, samples=1, width=512, height=512, img=None, mask=None):
    paths = []
    for _ in range(samples):
        image = Image.new("RGB", (width, height), tuple(np.random.randint(256, size=3)))
        with next_image_idx() as idx:
            path = os.path.join(dirname, image_names[idx])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        image.save(path)
        paths.append(path)
    return paths


def mock_gen_upscaled_image(
    input_image_path, output_dirname, new_width, original_prompt, upscale_engine="esrgan-v1-x2plus", verbose=True
):
    img = Image.open(input_image_path)
    new_height = int((img.height / img.width) * new_width)
    image = Image.new("RGB", (new_width, new_height), tuple(np.random.randint(256, size=3)))
    with next_image_idx() as idx:
        path = os.path.join(output_dirname, image_names[idx])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path)
    return [path]
