import os
import json
import logging
import yaml
from google import genai
from googleapiclient.discovery import build
from modules.database import get_past_topics, is_topic_used

def fetch_reference_titles() -> list:
    titles = []
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return [
            "महादेव का सबसे गुप्त ज्ञान: कैलाश संहिता का रहस्य",
            "मच्छिंद्रनाथ और नाथ संप्रदाय की उत्पत्ति का रहस्य",
            "ब्रह्मास्त्र कैसे बनता था? वैदिक अस्त्रों का विज्ञान",
            "भगवान चित्रगुप्त और कर्मों के लेखे-जोखे का रहस्य",
            "केदारनाथ मंदिर और अघोर साधना का अनसुना इतिहास"
        ]
    try:
        yt = build("youtube", "v3", developerKey=api_key)
        for handle in ["@SanatanKathalaya", "@zerotodreamofficial"]:
            res = yt.search().list(q=handle, type="video", part="snippet", maxResults=10, order="viewCount").execute()
            for item in res.get("items", []):
                titles.append(item["snippet"]["title"])
    except Exception as exc:
        logging.warning("Could not fetch optional reference titles: %s", exc)
    return titles


def select_unique_topic(video_type: str = "short") -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing required Gemini setting: GEMINI_API_KEY")
    with open("config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    past = get_past_topics(video_type, 60)
    ref_titles = fetch_reference_titles()
    client = genai.Client(api_key=api_key)
    prompt = f"""You are the Chief Research Strategist for the Hindi YouTube channel 'Avghad Baba India' (@avghadbabaaindia).
Channel Niche: Deep Devotional, Spiritual Research, Lord Shiva, Aghor/Nath traditions, Shiva Purana, Mahabharata mysteries, Ancient Temples, Bhagavad Gita philosophy.
Reference Trending Titles from @SanatanKathalaya and @zerotodreamofficial:
{json.dumps(ref_titles, ensure_ascii=False)}

Already covered topics (DO NOT REPEAT):
{json.dumps(past, ensure_ascii=False)}

Select ONE highly engaging, 100% original research topic for a {video_type.upper()} video in Hindi.
Clearly distinguish between historical facts, scripture references, and traditional beliefs.
Respond ONLY in valid JSON with keys:
"topic": (string in Hindi),
"category": (string),
"research_summary": (string in Hindi explaining scriptural/historical context),
"search_keywords_en": (list of 5 English visual keywords for stock footage like ["ancient temple india", "himalayas snow", "meditation silhouette", "lamp fire", "night stars"])
"""
    for attempt in range(3):
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        data = json.loads(resp.text)
        topic = data.get("topic")
        if not topic:
            raise ValueError("Gemini returned a topic without a topic value.")
        if not is_topic_used(topic, video_type):
            return data
        prompt += (
            f"\nThe topic '{topic}' was already used. Generate a genuinely different "
            "topic; do not alter or decorate the repeated topic."
        )
    raise RuntimeError("Gemini returned a previously used topic three times.")
