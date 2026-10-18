import os
import io
import urllib.parse
import requests
from PIL import Image, ImageDraw
from google import genai
from google.genai import types

def fetch_scene_visuals(scenes: list, video_type: str, out_dir: str) -> list:
    os.makedirs(out_dir, exist_ok=True)
    w, h = (1080, 1920) if video_type == "short" else (1920, 1080)
    aspect = "9:16" if video_type == "short" else "16:9"
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    paths = []

    for idx, scene in enumerate(scenes):
        query = scene.get("visual_query_en", "ancient hindu temple spiritual")
        prompt = f"Cinematic Indian devotional spiritual scene, {query}, divine atmosphere, ultra detailed, 8k, no text"
        img_path = os.path.join(out_dir, f"scene_{idx:02d}.jpg")
        generated = False

        # 1. Primary: Google Gemini Imagen API
        try:
            res = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    output_mime_type="image/jpeg",
                    aspect_ratio=aspect
                )
            )
            for g_img in res.generated_images:
                im = Image.open(io.BytesIO(g_img.image.image_bytes)).convert("RGB")
                im = im.resize((w, h), Image.Resampling.LANCZOS)
                im.save(img_path, "JPEG", quality=92)
                generated = True
                break
        except Exception:
            pass

        # 2. Automatic Free AI Backup (if Gemini free-tier image limit is reached)
        if not generated:
            try:
                p_clean = urllib.parse.quote(prompt)
                url = f"https://image.pollinations.ai/prompt/{p_clean}?width={w}&height={h}&nologo=true&seed={idx+202}"
                r = requests.get(url, timeout=25)
                if r.status_code == 200 and len(r.content) > 10000:
                    im = Image.open(io.BytesIO(r.content)).convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
                    im.save(img_path, "JPEG", quality=92)
                    generated = True
            except Exception:
                pass

        # 3. Offline Safe Fallback
        if not generated:
            img = Image.new("RGB", (w, h), (20, 10, 35))
            draw = ImageDraw.Draw(img)
            for y in range(h):
                draw.line([(0, y), (w, y)], fill=(int(25+(y/h)*70), int(12+(y/h)*30), int(40+(y/h)*90)))
            img.save(img_path, "JPEG", quality=92)

        paths.append(img_path)
    return paths
