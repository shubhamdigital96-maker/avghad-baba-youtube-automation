import os
import requests
from PIL import Image, ImageDraw, ImageFont

def generate_visual_for_scene(prompt: str, output_path: str, video_type: str = "short") -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    w, h = (1080, 1920) if video_type == "short" else (1920, 1080)
    
    # Clean prompt for search or fallback
    clean_query = prompt.split(',')[0].strip() or "Indian spiritual mythology"
    
    # Try fetching a high-quality free image from Wikimedia / Unsplash source / Picsum with seed
    image_saved = False
    
    # Method 1: Picsum photos with deterministic hash based on prompt text
    try:
        seed_val = abs(hash(prompt)) % 1000
        url = f"https://picsum.photos/seed/{seed_val}/{w}/{h}"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            image_saved = True
    except Exception:
        pass

    # Method 2: Fallback to stunning custom gradient image with spiritual theme if network fails
    if not image_saved:
        img = Image.new("RGB", (w, h), color=(15, 5, 25))
        draw = ImageDraw.Draw(img)
        
        # Draw rich spiritual gradient circles
        for i in range(h // 2):
            r = int(15 + (i / (h / 2)) * 40)
            g = int(5 + (i / (h / 2)) * 15)
            b = int(25 + (i / (h / 2)) * 60)
            draw.line([(0, i), (w, i)], fill=(r, g, b))
            draw.line([(0, h - i), (w, h - i)], fill=(r, g, b))
            
        # Add decorative text border / title concept
        try:
            font = ImageFont.load_default()
            draw.text((50, h // 2 - 50), "Avghad Baba India", fill=(255, 200, 50), font=font)
        except Exception:
            pass
            
        img.save(output_path, "JPEG")
        
    return output_path
