import os
import urllib.parse
from google_auth_oauthlib.flow import Flow

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

cid = "320264816317-bqm7lbdalo0prdt3rdf8l29gkc13hj13.apps.googleusercontent.com"
csec = input("\n1. अपना YOUTUBE_CLIENT_SECRET यहाँ पेस्ट करें और Enter दबाएँ: ").strip()

config = {
    "installed": {
        "client_id": cid,
        "client_secret": csec,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8080/"]
    }
}

flow = Flow.from_client_config(
    config,
    scopes=[
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly"
    ],
    redirect_uri="http://localhost:8080/"
)

auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
print("\n" + "="*65)
print("2. नीचे दिए गए नीले लिंक पर क्लिक करके अपने चैनल से Allow करें:")
print(auth_url)
print("="*65)

raw_input = input("\n3. Allow करने के बाद जो पेज खुले, उसके ऊपर Address Bar का पूरा लिंक (URL) कॉपी करके यहाँ पेस्ट करें और Enter दबाएँ:\n👉 ").strip()

if "code=" in raw_input:
    parsed = urllib.parse.urlparse(raw_input)
    code = urllib.parse.parse_qs(parsed.query).get("code", [raw_input])[0]
else:
    code = raw_input

flow.fetch_token(code=code)
print("\n" + "="*65)
print("✅ बधाई हो! आपका YOUTUBE_REFRESH_TOKEN नीचे है (इसे कॉपी करके GitHub Secrets में सेव करें):")
print(flow.credentials.refresh_token)
print("="*65 + "\n")
