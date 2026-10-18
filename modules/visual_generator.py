import os
from PIL import Image, ImageDraw, ImageFilter

def fetch_scene_visuals(scenes: list, video_type: str, out_dir: str) -> list:
    os.makedirs(out_dir, exist_ok=True)
    w, h = (1080, 1920) if video_type == "short" else (1920, 1080)
    paths = []

    # Rich spiritual Indian color palettes for professional devotional videos
    palettes = [
        ((235, 110, 20), (80, 10, 5)),      # Divine Saffron & Deep Maroon
        ((15, 20, 55), (120, 60, 10)),      # Cosmic Night & Temple Gold
        ((180, 40, 40), (20, 10, 40)),      # Sacred Flame & Spiritual Purple
        ((240, 170, 30), (50, 20, 10)),     # Temple Brass & Deep Ochre
        ((20, 50, 80), (10, 10, 20))        # Holy River & Deep Night
    ]

    for idx, scene in enumerate(scenes):
        img_path = os.path.join(out_dir, f"scene_{idx:02d}.jpg")
        col1, col2 = palettes[idx % len(palettes)]

        # Create high-end cinematic spiritual gradient background
        img = Image.new("RGB", (w, h), col1)
        draw = ImageDraw.Draw(img)

        # Vertical gradient blend
        for y in range(h):
            factor = y / h
            r = int(col1[0] * (1 - factor) + col2[0] * factor)
            g = int(col1[1] * (1 - factor) + col2[1] * factor)
            b = int(col1[2] * (1 - factor) + col2[2] * factor)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        # Add sacred divine light aura / halo in the center
        halo_radius = w // 3
        for r_val in range(halo_radius, 0, -5):
            alpha = int(25 * (1 - r_val / halo_radius))
            draw.ellipse(
                [w//2 - r_val, h//2 - r_val, w//2 + r_val, h//2 + r_val],
                outline=(255, 220, 100, alpha), width=3
            )

        img = img.filter(ImageFilter.GaussianBlur(1))
        img.save(img_path, "JPEG", quality=95)
        paths.append(img_path)

    return paths
