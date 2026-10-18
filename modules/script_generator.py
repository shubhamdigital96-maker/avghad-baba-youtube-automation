import os
import json
from google import genai
from google.genai import errors

def generate_script_and_metadata(topic: str, video_type: str = "short") -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key) if api_key else genai.Client()
    
    prompt = f"""
    Create a highly engaging YouTube {'Short' if video_type == 'short' else 'Long'} script in Hindi about: "{topic}" for the channel "Avghad Baba India".
    Return ONLY a valid JSON object with the following keys:
    - "title": Catchy YouTube title in Hindi with emojis.
    - "description": Video description with hashtags.
    - "tags": List of tags.
    - "scenes": List of objects, each having "narration" (Hindi text) and "visual" (English image prompt description).
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception as e:
        # Fallback if quota / rate limit (429) or any API error occurs
        print(f"Warning: Gemini API failed ({e}). Using robust fallback script generation.")
        return {
            "title": f"रहस्यमय सनातन कथा: {topic} 🙏 #AvghadBabaIndia",
            "description": f"जानें {topic} का अद्भुत और अनकहा रहस्य। सनातन धर्म और पौराणिक कथाओं के लिए सब्सक्राइब करें Avghad Baba India। #shorts #Shiva #Mythology",
            "tags": ["Avghad Baba India", "Mythology", "Shiva", "Sanatan", "Shorts"],
            "scenes": [
                {"narration": f"आइए जानते हैं {topic} के इस महान और गुप्त रहस्य के बारे में।", "visual": "mystical cosmic spiritual background glowing energy"},
                {"narration": "यह कथा हमारे सनातन इतिहास का एक अत्यंत महत्वपूर्ण और शक्तिशाली हिस्सा है।", "visual": "ancient sacred Indian temple divine atmosphere"},
                {"narration": "हर हर महादेव! ऐसे ही रहस्यों के लिए चैनल को सब्सक्राइब करें।", "visual": "divine light shiva trishul background"}
            ]
        }
