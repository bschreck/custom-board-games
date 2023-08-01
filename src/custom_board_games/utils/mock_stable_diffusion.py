from PIL import Image
import numpy as np
import os

image_names = [f"{i}.png" for i in range(100)]
image_idx = [0]


def gen_stability_image_from_text(prompt, name, dirname, samples=1, width=512, height=512, img=None, mask=None):
    paths = []
    for _ in range(samples):
        image = Image.new("RGB", (512, 512), tuple(np.random.randint(256, size=3)))
        path = os.path.join(dirname, name, image_names[image_idx[0]])
        image_idx[0] += 1
        os.makedirs(os.path.dirname(path), exist_ok=True)
        image.save(path)
        paths.append(path)
    return paths
