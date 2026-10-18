import os
import logging
import yaml
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def get_authenticated_service():
    required_env = (
        "YOUTUBE_REFRESH_TOKEN",
        "YOUTUBE_CLIENT_ID",
        "YOUTUBE_CLIENT_SECRET",
    )
    missing = [name for name in required_env if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing YouTube authentication settings: {', '.join(missing)}")
    creds = Credentials(
        None,
        refresh_token=os.getenv("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("YOUTUBE_CLIENT_ID"),
        client_secret=os.getenv("YOUTUBE_CLIENT_SECRET"),
        scopes=[
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly"
        ]
    )
    return build("youtube", "v3", credentials=creds)

def verify_destination_channel(youtube) -> tuple[bool, str]:
    resp = youtube.channels().list(part="snippet", mine=True).execute()
    items = resp.get("items", [])
    if not items:
        return False, "No YouTube channel found for these credentials."
    ch = items[0]
    title = ch["snippet"].get("title", "")
    custom_url = (ch["snippet"].get("customUrl") or "").lower()
    if "avghad" not in title.lower() and "avghad" not in custom_url:
        return False, f"SAFETY BLOCK: Authenticated channel '{title}' ({custom_url}) does not match Avghad Baba India!"
    return True, f"Verified channel: {title} ({custom_url})"

def upload_video(mp4_path: str, thumb_path: str, seo_data: dict, video_type: str) -> str:
    with open("config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    youtube = get_authenticated_service()
    ok, msg = verify_destination_channel(youtube)
    if not ok:
        raise RuntimeError(msg)

    privacy = "public" if cfg["publishing"].get("public_approved", False) else "private"
    body = {
        "snippet": {
            "title": seo_data["title"][:100],
            "description": seo_data["description"],
            "tags": seo_data.get("tags", []),
            "categoryId": seo_data.get("categoryId", "27"),
            "defaultLanguage": "hi",
            "defaultAudioLanguage": "hi"
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(mp4_path, chunksize=1024*1024, resumable=True, mimetype="video/mp4")
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = req.next_chunk()

    video_id = response["id"]
    if os.path.exists(thumb_path):
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumb_path, mimetype="image/jpeg")
            ).execute()
        except Exception as exc:
            logging.warning(
                "Video %s uploaded, but its custom thumbnail could not be set: %s",
                video_id,
                exc,
            )
    return video_id
