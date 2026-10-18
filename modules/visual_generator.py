import os
import requests
from PIL import Image, ImageDraw, ImageFilter
import random

def fetch_scene_visuals(scenes: list, video_type: str, out_dir: str) -> list:
    os.makedirs(out_dir, exist_ok=True)
    w, h = (1080, 1920) if video_type == "short" else (1920, 1080)
    orientation = "portrait" if video_type == "short" else "landscape"
    pexels_key = os.getenv("PEXELS_API_KEY", "")
    pixabay_key = os.getenv("PIXABAY_API_KEY", "")
    paths = []

    for idx, scene in enumerate(scenes):
        query = scene.get("visual_query_en", "spiritual meditation nature")
        img_path = os.path.join(out_dir, f"scene_{idx:02d}.jpg")
        downloaded = False

        if pexels_key:
            try:
                r = requests.get(
                    "https://api.pexels.com/v1/search",
                    headers={"Authorization": pexels_key},
                    params={"query": query, "orientation": orientation, "per_page": 3},
                    timeout=10
                )
                photos = r.json().get("photos", [])
                if photos:
                    img_url = random.choice(photos)["src"]["large2x"]
                    img_data = requests.get(img_url, timeout=15).content
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                    downloaded = True
            except Exception:
                pass

        if not downloaded and pixabay_key:
            try:
                r = requests.get(
                    "https://pixabay.com/api/",
                    params={"key": pixabay_key, "q": query, "image_type": "photo", "per_page": 3},
                    timeout=10
                )
                hits = r.json().get("hits", [])
                if hits:
                    img_url = random.choice(hits)["largeImageURL"]
                    img_data = requests.get(img_url, timeout=15).content
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                    downloaded = True
            except Exception:
                pass

        if not downloaded:
            img = Image.new("RGB", (w, h), (15, 10, 30))
            draw = ImageDraw.Draw(img)
            for y in range(h):
                r_col = int(20 + (y / h) * 60)
                g_col = int(10 + (y / h) * 25)
                b_col = int(35 + (y / h) * 80)
                draw.line([(0, y), (w, y)], fill=(r_col, g_col, b_col))
            img = img.filter(ImageFilter.GaussianBlur(2))
            img.save(img_path, "JPEG", quality=92)
        else:
            im = Image.open(img_path).convert("RGB")
            im = im.resize((w, h), Image.Resampling.LANCZOS)
            im.save(img_path, "JPEG", quality=92)

        paths.append(img_path)
    return paths
