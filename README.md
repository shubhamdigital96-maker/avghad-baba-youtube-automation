# Avghad Baba India - YouTube Video Automation

Automates Hindi devotional and spiritual video production and uploads exclusively to YouTube.

## What the pipeline does

1. Generates a researched Hindi topic, script, SEO metadata, and scene-specific visual prompts.
2. Synthesizes each narration scene separately, then combines the audio and offsets its Hindi word-timed subtitles.
3. Generates cinematic scene images and holds each image for the duration of its matching narration.
4. Renders a 9:16 Short or 16:9 long video with a slow camera move, burned-in Devanagari captions, and synced narration.
5. Checks the output dimensions, audio/video duration sync, and metadata before uploading to the configured YouTube channel.
6. Uploads a custom thumbnail when YouTube accepts it. Thumbnail upload failures are logged without losing a successful video upload.

Generated scene images use Pollinations. If an image cannot be generated, the run fails rather than publishing a placeholder video.

## Setup

- Python 3.11+
- FFmpeg with `libass` and `libmp3lame`, plus the Noto Sans Devanagari fonts
- Set `GEMINI_API_KEY`, `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, and `YOUTUBE_REFRESH_TOKEN` as environment variables or GitHub Actions secrets.
- The optional `YOUTUBE_API_KEY` enables reference-video research.
- Install Python dependencies with `pip install -r requirements.txt`.

Run a local production check without uploading:

```sh
python main.py --type short --dry-run
```

GitHub Actions runs Shorts at 09:00, 13:00, and 18:00 IST and a long video at 20:00 IST. Scheduled uploads remain **private** unless `publishing.public_approved` in `config.yaml` is explicitly enabled. Manual runs can choose `short` or `long`.
