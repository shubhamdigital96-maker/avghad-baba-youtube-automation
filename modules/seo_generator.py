import os
import json
from google import genai

def generate_seo_metadata(topic_data: dict, script_data: dict, video_type: str = "short") -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing required Gemini setting: GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    prompt = f"""Generate high-CTR, policy-safe YouTube SEO metadata in Hindi for 'Avghad Baba India' (@avghadbabaaindia).
Topic: {topic_data['topic']}
Video Type: {video_type}
Hook: {script_data['hook']}

Return ONLY valid JSON:
{{
  "title": "Compelling Hindi + English title under 90 chars (append #shorts if video_type is short)",
  "description": "Detailed Hindi description with spiritual disclaimer, key takeaways, and hashtags",
  "tags": ["avghad baba india", "sanatan dharma", "lord shiva", "hindu mythology", "spiritual hindi"],
  "categoryId": "27"
}}"""
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    return json.loads(resp.text)
