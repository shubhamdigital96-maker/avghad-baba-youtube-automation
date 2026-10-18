import os
import requests
import logging

def publish_to_facebook(video_path: str, caption: str):
    page_id = os.environ.get("FB_PAGE_ID")
    access_token = os.environ.get("FB_PAGE_ACCESS_TOKEN")

    if not page_id or not access_token:
        logging.warning("⚠️ Facebook credentials (FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN) not found. Skipping FB upload.")
        return False

    url = f"https://graph-video.facebook.com/v18.0/{page_id}/videos"
    
    payload = {
        "description": caption,
        "access_token": access_token
    }
    
    try:
        logging.info("📤 Uploading video to Facebook Page...")
        with open(video_path, "rb") as video_file:
            files = {"source": video_file}
            response = requests.post(url, data=payload, files=files, timeout=120)
            
        res_data = response.json()
        if "id" in res_data:
            logging.info(f"✅ Successfully uploaded to Facebook! Video ID: {res_data['id']}")
            return True
        else:
            logging.error(f"❌ Facebook upload failed: {res_data}")
            return False
    except Exception as e:
        logging.error(f"❌ Error uploading to Facebook: {e}")
        return False
