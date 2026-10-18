import os
import json
import subprocess

def verify_video_quality(mp4_path: str, video_type: str, seo_data: dict) -> tuple[bool, str]:
    if not os.path.exists(mp4_path) or os.path.getsize(mp4_path) < 50000:
        return False, "MP4 file missing or too small."
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=codec_type,width,height:format=duration",
        "-of", "json", mp4_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return False, "FFprobe failed to read video."
    info = json.loads(res.stdout)
    streams = info.get("streams", [])
    has_video = any(s.get("codec_type") == "video" for s in streams)
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    if not (has_video and has_audio):
        return False, "Missing video or audio stream."

    v_stream = next(s for s in streams if s.get("codec_type") == "video")
    w, h = v_stream.get("width"), v_stream.get("height")
    exp_w, exp_h = (1080, 1920) if video_type == "short" else (1920, 1080)
    if (w, h) != (exp_w, exp_h):
        return False, f"Resolution mismatch: got {w}x{h}, expected {exp_w}x{exp_h}"

    dur = float(info.get("format", {}).get("duration", 0))
    if dur < 10:
        return False, f"Video too short: {dur}s"
    if not seo_data.get("title") or not seo_data.get("description"):
        return False, "Incomplete SEO metadata."

    return True, f"Passed all checks ({w}x{h}, {dur:.1f}s)"
