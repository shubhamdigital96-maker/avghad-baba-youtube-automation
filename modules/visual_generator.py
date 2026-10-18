import io
import os
import urllib.parse
import requests
from PIL import Image, ImageDraw, ImageOps

def fetch_scene_visuals(scenes: list, video_type: str, out_dir: str) -> list:
    os.makedirs(out_dir, exist_ok=True)
    w, h = (1080, 1920) if video_type == "short" else (1920, 1080)
    paths = []

    for idx, scene in enumerate(scenes):
        img_path = os.path.join(out_dir, f"scene_{idx:02d}.jpg")
        raw_query = scene.get("visual_query_en", "").strip()
        if not raw_query:
            raise ValueError(f"Scene {idx + 1} has no visual search query.")
        query = (
            f"{raw_query}, premium cinematic devotional photography, "
            "dramatic natural lighting, rich saffron and deep indigo color grading, "
            "high detail, tasteful Indian spiritual atmosphere, no text, no watermark"
        )
        try:
            encoded_q = urllib.parse.quote(query)
            img_url = f"https://image.pollinations.ai/prompt/{encoded_q}?width={w}&height={h}&nologo=true&seed={idx+777}"
            response = requests.get(img_url, timeout=90)
            response.raise_for_status()
            if len(response.content) < 12_000:
                raise ValueError("The generated image response was unexpectedly small.")
            with Image.open(io.BytesIO(response.content)) as source:
                image = ImageOps.fit(
                    source.convert("RGB"),
                    (w, h),
                    method=Image.Resampling.LANCZOS,
                    centering=(0.5, 0.45),
                )
                draw = ImageDraw.Draw(image)
                draw.rectangle([(0, 0), (w - 1, h - 1)], outline=(255, 205, 105), width=5)
                image.save(img_path, "JPEG", quality=94, optimize=True)
        except (requests.RequestException, OSError, ValueError) as exc:
            raise RuntimeError(f"Could not create visual for scene {idx + 1}: {exc}") from exc

        paths.append(img_path)
    return paths
