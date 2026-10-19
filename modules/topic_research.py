import os
from google import genai
from modules.database import is_topic_used

FALLBACK_TOPICS = [
    "भगवान शिव का 'शरभ अवतार': जब महादेव ने धारण किया सिंह-पक्षी का भयानक रूप",
    "मणिकर्णिका घाट का महाश्मशान: मृत्यु के समय महादेव कान में कौन सा तारक मंत्र फूंकते हैं?",
    "कालभैरव का प्राकट्य और कपाल मोचन का रहस्य: महादेव ने ब्रह्मा का सिर क्यों काटा?",
    "भगवान शिव की तीसरी आँख खुलने का रहस्य और प्रलय का तांडव",
    "अमरनाथ गुफा के रहस्य: जहाँ महादेव ने अमर कथा सुनाई थी",
    "रुद्राक्ष की उत्पत्ति कैसे हुई? शिव के आंसुओं से जुड़ा रहस्य"
]

def select_unique_topic(video_type: str = "short") -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key) if api_key else genai.Client()
    
    prompt = f"""
    Suggest a unique, highly engaging, and viral Hindi YouTube {'Short' title/topic} about Lord Shiva, Sanatan mythology, or secret Puranic legends for the channel 'Avghad Baba India'.
    Return ONLY the topic title in Hindi, nothing else. Do not repeat common topics.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )
        topic = response.text.strip().replace('"', '').replace("'", "")
        if topic and not is_topic_used(topic, video_type):
            return topic
    except Exception as e:
        print(f"Warning: Topic research Gemini API failed ({e}). Using fallback topic pool.")
        
    # Fallback to unused topic from pool
    for t in FALLBACK_TOPICS:
        if not is_topic_used(t, video_type):
            return t
            
    return FALLBACK_TOPICS[0]
