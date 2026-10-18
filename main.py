import os
import sys
import argparse
import yaml
from dotenv import load_dotenv
from modules.database import init_db, record_publication
from modules.topic_research import select_unique_topic
from modules.script_generator import generate_script
from modules.voice_generator import generate_voiceover
from modules.visual_generator import fetch_scene_visuals
from modules.video_generator import render_video
from modules.thumbnail_generator import create_thumbnail
from modules.seo_generator import generate_seo_metadata
from modules.quality_checker import verify_video_quality
from modules.youtube_publisher import upload_video
from modules.notification_service import notify

def run_pipeline(video_type: str = "short", dry_run: bool = False):
    load_dotenv()
    init_db()
    os.makedirs("output", exist_ok=True)
    try:
        notify(f"Starting {video_type.upper()} pipeline for Avghad Baba India...")
        topic_data = select_unique_topic(video_type)
        notify(f"Selected Topic: {topic_data['topic']}")

        script_data = generate_script(topic_data, video_type)
        scenes = script_data.get("scenes", [])
        if not scenes:
            raise ValueError("Script generation returned no scenes.")
        audio_path = f"output/narration_{video_type}.mp3"
        subs_path = f"output/subs_{video_type}.srt"
        scene_durations = generate_voiceover(
            script_data["full_narration"],
            audio_path,
            subs_path,
            scenes=scenes,
        )

        images = fetch_scene_visuals(scenes, video_type, f"output/scenes_{video_type}")
        mp4_path = f"output/final_{video_type}.mp4"
        render_video(
            images,
            audio_path,
            subs_path,
            mp4_path,
            video_type,
            scene_durations=scene_durations,
        )

        thumb_path = f"output/thumb_{video_type}.jpg"
        create_thumbnail(images[0], topic_data["topic"], thumb_path)

        seo_data = generate_seo_metadata(topic_data, script_data, video_type)
        passed, qc_msg = verify_video_quality(mp4_path, video_type, seo_data)
        if not passed:
            raise RuntimeError(f"Quality Control Failed: {qc_msg}")
        notify(f"Quality Control Passed: {qc_msg}")

        if dry_run:
            notify("Dry run completed successfully. Skipping YouTube upload.")
            return

        video_id = upload_video(mp4_path, thumb_path, seo_data, video_type)
        with open("config.yaml", "r", encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)
        privacy = "public" if config["publishing"].get("public_approved", False) else "private"
        record_publication(topic_data["topic"], video_type, seo_data["title"], video_id, privacy)
        notify(f"Successfully uploaded! YouTube Video ID: {video_id}")
    except Exception as e:
        notify(str(e), is_error=True)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["short", "long"], default="short")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run_pipeline(args.type, args.dry_run)
