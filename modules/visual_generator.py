import os
import urllib.parse
import requests
from PIL import Image, ImageDraw, ImageFilter

def fetch_scene_visuals(scenes: list, video_type: str, out_dir: str) -> list:
    os.makedirs(out_dir, exist_ok=True)
    w, h = (1080, 1920) if video_type == "short" else (1920, 1080)
    paths = []
    
    # High-quality curated spiritual keywords fallback list
    fallback_keywords = [
        "ancient indian shiva temple Himalayas dramatic lighting",
        "holy sadhu meditating in himalayas mountains",
        "divine glowing shiva lingam with sacred fire",
        "mystical ancient Indian temple pillars at night",
        "sacred river ganga aarti with glowing lamps",
        "cosmic universe spiritual meditation aura glow"
    ]

    for idx, scene in enumerate(scenes):
        raw_query = scene.get("visual_query_en", "ancient hindu temple")
        query = f"{raw_query} indian devotional spiritual cinematic 8k"
        img_path = os.path.join(out_dir, f"scene_{idx:02d}.jpg")
        downloaded = False

        # 1. Primary High-Res AI Art Engine (Pollinations AI - Fast & Never Fails)
        try:
            encoded_query = urllib.parse.quote(query)
            ai_url = f"https://image.pollinations.ai/prompt/{encoded_query}?width={w}&height={h}&nologo=true&seed={idx+33}"
            r = requests.get(ai_url, timeout=20)
            if r.status_code == 200 and len(r.content) > 8000:
                with open(img_path, "wb") as f:
                    f.write(r.content)
                # Verify it's a valid image
                Image.open(img_path).verify()
                downloaded = True
        except Exception:
            pass

        # 2. Secondary Reliable Backup (Unsplash Source for real spiritual/temple photos)
        if not downloaded:
            try:
                backup_q = urllib.parse.quote(fallback_keywords[idx % len(fallback_keywords)])
                unsplash_url = f"https://source.unsplash.com/{w}x{h}/?{backup_q}"
                r = requests.get(unsplash_url, timeout=15)
                if r.status_code == 200 and len(r.content) > 8000:
                    with open(img_path, "wb") as f:
                        f.write(r.content)
                    Image.open(img_path).verify()
                    downloaded = True
            except Exception:
                pass

        # 3. Ultimate Rich Gradient Art with Glow (If all internet fetches fail)
        if not downloaded:
            img = Image.new("RGB", (w, h), (10, 5, 25))
            draw = ImageDraw.Draw(img)
            # Create a rich vertical spiritual gradient
            for y in range(h):
                factor = y / h
                r_c = int(20 + factor * 80)
                g_c = int(10 + factor * 30)
                b_c = int(45 + factor * 110)
                draw.line([(0, y), (w, y)], fill=(r_c, g_c, b_c))
            # Draw a glowing circle in center
            draw.ellipse([w//2 - 150, h//2 - 150, w//2 + 150, h//2 + 150], fill=(255, 180, 50, 100))
            img.save(img_path, "JPEG", quality=95)

        # Ensure correct size
        try:
            im = Image.open(img_path).convert("RGB")
            im = im.resize((w, h), Image.Resampling.LANCZOS)
            im.save(img_path, "JPEG", quality=95)
        except Exception:
            pass

        paths.append(img_path)
    return paths
