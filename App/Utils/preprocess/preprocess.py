from PIL import Image
import numpy as np

def preprocess_image(image, target_shape):
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize((target_shape[3], target_shape[2]), Image.Resampling.LANCZOS)
    image_np = np.array(image).astype(np.float32)
    image_np = image_np / 255.0
    image_np = image_np.transpose((2, 0, 1))
    image_np = np.expand_dims(image_np, axis=0)
    return image_np