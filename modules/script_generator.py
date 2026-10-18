import os
import json
from google import genai

def generate_script(topic_data: dict, video_type: str = "short") -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing required Gemini setting: GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    scenes_count = "5 to 6 concise scenes (total 90-115 Hindi words, ~40-50 seconds)" if video_type == "short" else "14 to 18 detailed scenes (total 750-950 Hindi words, ~5-6 minutes)"
    prompt = f"""Write a powerful, factually responsible, deeply engaging 100% original Hindi script for 'Avghad Baba India'.
Topic: {topic_data['topic']}
Context: {topic_data['research_summary']}
Format: {video_type.upper()} ({scenes_count})

Rules:
1. Strong spiritual/mystery hook in the first 3 seconds.
2. Pure, natural spoken Hindi (Devanagari script) suitable for deep narration.
3. Never invent fake scripture verses. Cite texts respectfully as traditional/puranic accounts.
4. End with a devotional reflection (e.g., 'हर हर महादेव' या 'जय श्री कृष्ण').

Return ONLY valid JSON:
{{
  "hook": "opening line in Hindi",
  "scenes": [
    {{
      "narration": "Hindi spoken line for this scene",
      "subtitle_short": "Short punchy Hindi text for screen",
      "visual_query_en": "English search term for Pexels/Pixabay video (e.g. 'himalayas mountains', 'indian temple', 'fire flames')"
    }}
  ],
  "full_narration": "Complete combined Hindi narration with natural punctuation"
}}"""
    resp = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    return json.loads(resp.text)
