from collections import deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(r"C:\Users\RentalLink\Downloads")
TARGET = ROOT / "assets"
ICONS = {
    "nav-home.png": "image (1).png",
    "nav-map.png": "image (2).png",
    "nav-mission.png": "image (3).png",
    "nav-collection.png": "image.png",
}


def is_background(pixel):
    red, green, blue, alpha = pixel
    return alpha > 0 and min(red, green, blue) >= 232 and max(red, green, blue) - min(red, green, blue) <= 18


def make_icon(source, destination):
    image = Image.open(source).convert("RGBA")
    width, height = image.size
    pixels = image.load()
    visited = set()
    queue = deque()
    for x in range(width):
        queue.extend(((x, 0), (x, height - 1)))
    for y in range(height):
        queue.extend(((0, y), (width - 1, y)))
    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or not (0 <= x < width and 0 <= y < height) or not is_background(pixels[x, y]):
            continue
        visited.add((x, y))
        pixels[x, y] = (*pixels[x, y][:3], 0)
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    alpha = image.getchannel("A")
    box = alpha.getbbox()
    if not box:
        raise RuntimeError(f"No icon subject detected: {source}")
    pad = max(12, round(max(box[2] - box[0], box[3] - box[1]) * .06))
    box = (max(0, box[0] - pad), max(0, box[1] - pad), min(width, box[2] + pad), min(height, box[3] + pad))
    image = image.crop(box)
    image.thumbnail((256, 256), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (256, 256))
    canvas.alpha_composite(image, ((256 - image.width) // 2, (256 - image.height) // 2))
    canvas.save(destination, "PNG", optimize=True)


TARGET.mkdir(exist_ok=True)
for output, input_name in ICONS.items():
    make_icon(SOURCE / input_name, TARGET / output)
    print(TARGET / output)
