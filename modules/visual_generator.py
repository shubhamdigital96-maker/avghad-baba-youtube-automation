import os
import hashlib
import io
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps


def generate_visual_for_scene(prompt: str, output_path: str, video_type: str = "short") -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    w, h = (1080, 1920) if video_type == "short" else (1920, 1080)

    clean_query = prompt.split(',')[0].strip() or "Indian spiritual mythology"

    try:
        seed_val = int(hashlib.sha256(clean_query.encode("utf-8")).hexdigest()[:8], 16) % 1000
        url = f"https://picsum.photos/seed/{seed_val}/{w}/{h}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        with Image.open(io.BytesIO(response.content)) as source:
            image = source.convert("RGB")
            image = ImageOps.fit(image, (w, h), method=Image.Resampling.LANCZOS)
            image.save(output_path, "JPEG", quality=92)
    except Exception:
        _generate_spiritual_fallback(output_path, (w, h))

    return output_path


def _generate_spiritual_fallback(output_path: str, size: tuple[int, int]) -> None:
    width, height = size
    image = Image.new("RGB", size)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        blend = y / max(1, height - 1)
        color = (
            int(12 + 34 * blend),
            int(6 + 14 * blend),
            int(32 + 54 * blend),
        )
        draw.line((0, y, width, y), fill=color)

    draw = ImageDraw.Draw(image, "RGBA")
    center = (width // 2, height // 2)
    radius = min(width, height) // 4
    for inset in range(0, radius, max(8, radius // 24)):
        alpha = max(30, 170 - int(140 * inset / max(1, radius)))
        draw.ellipse(
            (
                center[0] - radius + inset,
                center[1] - radius + inset,
                center[0] + radius - inset,
                center[1] + radius - inset,
            ),
            outline=(255, 191, 64, alpha),
            width=max(2, radius // 60),
        )
    for index in range(12):
        angle = index * 30
        draw.arc(
            (
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
            ),
            start=angle,
            end=angle + 15,
            fill=(255, 220, 130, 180),
            width=max(2, radius // 50),
        )

    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
            max(24, width // 20),
        )
        label = "हर हर महादेव"
    except OSError:
        font = ImageFont.load_default()
        label = "AVGHAD BABA INDIA"
    bounds = draw.textbbox((0, 0), label, font=font)
    draw.text(
        (center[0] - (bounds[2] - bounds[0]) // 2, center[1] + radius + 20),
        label,
        fill=(255, 224, 145, 255),
        font=font,
    )
    image.save(output_path, "JPEG", quality=92)


def fetch_scene_visuals(scenes: list, video_type: str, output_dir: str) -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []
    for index, scene in enumerate(scenes):
        prompt = scene.get("visual_query_en") or scene.get("narration", "")
        output_path = os.path.join(output_dir, f"scene_{index + 1:03d}.jpg")
        image_paths.append(generate_visual_for_scene(prompt, output_path, video_type))
    return image_paths
