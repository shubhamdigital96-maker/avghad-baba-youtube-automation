from PIL import Image, ImageDraw, ImageFont

def create_thumbnail(bg_image_path: str, title_hindi: str, out_path: str) -> str:
    im = Image.open(bg_image_path).convert("RGB").resize((1280, 720), Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 135))
    im = im.convert("RGBA")
    im = Image.alpha_composite(im, overlay).convert("RGB")
    draw = ImageDraw.Draw(im)

    draw.rectangle([(30, 30), (1250, 690)], outline=(255, 180, 0), width=6)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf", 64)
        brand_font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf", 36)
    except Exception:
        font = ImageFont.load_default()
        brand_font = ImageFont.load_default()

    words = title_hindi.split()
    lines = [" ".join(words[i:i+4]) for i in range(0, min(len(words), 12), 4)]
    y_text = 220
    for line in lines:
        draw.text((84, y_text + 4), line, font=font, fill=(0, 0, 0))
        draw.text((80, y_text), line, font=font, fill=(255, 230, 80))
        y_text += 95

    draw.text((80, 610), "AVGHAD BABA INDIA", font=brand_font, fill=(255, 255, 255))
    im.save(out_path, "JPEG", quality=95)
    return out_path
