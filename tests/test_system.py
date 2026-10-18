import os, sys; sys.path.insert(0, os.getcwd())
import json
from types import SimpleNamespace
from modules.database import init_db, record_publication, is_topic_used

def test_duplicate_prevention(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.database.DB_PATH", str(tmp_path / "publication_history.db"))
    init_db()
    sample_topic = "कैलाश संहिता परीक्षण विषय 101"
    record_publication(sample_topic, "short", "Test Title", "vid123", "private")
    assert is_topic_used(sample_topic) is True


def test_legacy_publications_migrate_into_active_database(tmp_path, monkeypatch):
    import sqlite3
    import modules.database as database

    legacy_path = tmp_path / "legacy.db"
    legacy_conn = sqlite3.connect(legacy_path)
    legacy_conn.execute(
        """
        CREATE TABLE history (
            topic TEXT, video_type TEXT, title TEXT, youtube_id TEXT,
            privacy_status TEXT, created_at TEXT
        )
        """
    )
    legacy_conn.execute(
        "INSERT INTO history VALUES (?, ?, ?, ?, ?, ?)",
        ("पुराना विषय", "short", "पुराना शीर्षक", "old123", "private", "2025-01-01T00:00:00+00:00"),
    )
    legacy_conn.commit()
    legacy_conn.close()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(database, "DB_PATH", "database.db")
    monkeypatch.setattr(database, "LEGACY_DB_PATH", str(legacy_path))

    database.init_db()
    database.init_db()

    conn = sqlite3.connect("database.db")
    try:
        assert conn.execute("SELECT COUNT(*) FROM published_videos").fetchone()[0] == 1
    finally:
        conn.close()


def test_scene_frame_allocation_matches_audio_duration():
    from modules.video_generator import _allocate_scene_frames

    assert _allocate_scene_frames([1.0, 2.0, 3.0], 6.0, 25) == [25, 50, 75]


def test_scene_frame_allocation_covers_final_partial_frame():
    from modules.video_generator import _allocate_scene_frames

    assert sum(_allocate_scene_frames([1.0, 1.0], 2.01, 25)) == 51


def test_scene_frame_allocation_rejects_invalid_durations():
    import pytest
    from modules.video_generator import _allocate_scene_frames

    with pytest.raises(ValueError, match="positive audio duration"):
        _allocate_scene_frames([1.0, 0.0], 1.0, 25)


def test_scene_frame_allocation_keeps_every_scene_and_total_frames():
    from modules.video_generator import _allocate_scene_frames

    frames = _allocate_scene_frames([100.0, 0.001], 1.0, 25)

    assert len(frames) == 2
    assert min(frames) >= 1
    assert sum(frames) == 25


def test_scene_subtitles_are_shifted_by_prior_audio_duration(tmp_path):
    from modules.voice_generator import _combine_subtitles

    first = tmp_path / "first.srt"
    second = tmp_path / "second.srt"
    combined = tmp_path / "combined.srt"
    first.write_text("1\n00:00:00,000 --> 00:00:00,500\nपहला दृश्य\n", encoding="utf-8")
    second.write_text("1\n00:00:00,100 --> 00:00:00,600\nदूसरा दृश्य\n", encoding="utf-8")

    _combine_subtitles([str(first), str(second)], [1.25, 1.5], str(combined))

    assert "2\n00:00:01,350 --> 00:00:01,850\nदूसरा दृश्य" in combined.read_text(encoding="utf-8")


def test_voice_generator_returns_audio_duration_per_scene(tmp_path, monkeypatch):
    from modules import voice_generator

    async def generate_scene(text, audio_path, subtitle_path):
        open(audio_path, "wb").close()
        subtitle = "1\n00:00:00,100 --> 00:00:00,600\n" + text + "\n"
        with open(subtitle_path, "w", encoding="utf-8") as subtitle_file:
            subtitle_file.write(subtitle)

    durations = iter([1.0, 2.0])
    monkeypatch.setattr(voice_generator, "_generate_scene_voiceover", generate_scene)
    monkeypatch.setattr(voice_generator, "_get_audio_duration", lambda path: next(durations))

    def fake_run(command, **kwargs):
        open(command[-1], "wb").close()

    monkeypatch.setattr(voice_generator.subprocess, "run", fake_run)
    audio_path = tmp_path / "narration.mp3"
    subtitle_path = tmp_path / "narration.srt"
    result = voice_generator.generate_voiceover(
        "पहला दृश्य दूसरा दृश्य",
        str(audio_path),
        str(subtitle_path),
        scenes=[{"narration": "पहला दृश्य"}, {"narration": "दूसरा दृश्य"}],
    )

    assert result == [1.0, 2.0]
    assert audio_path.exists()
    assert "2\n00:00:01,100 --> 00:00:01,600\nदूसरा दृश्य" in subtitle_path.read_text(
        encoding="utf-8"
    )


def test_edge_tts_requests_word_boundaries(tmp_path, monkeypatch):
    import asyncio
    from modules import voice_generator

    class FakeCommunicate:
        def __init__(self, text, voice, *, boundary):
            assert voice == "hi-IN-SwaraNeural"
            assert boundary == "WordBoundary"

        async def stream(self):
            yield {"type": "audio", "data": b"audio"}
            yield {
                "type": "WordBoundary",
                "offset": 0,
                "duration": 5_000_000,
                "text": "महादेव",
            }

    monkeypatch.setattr(voice_generator.edge_tts, "Communicate", FakeCommunicate)
    audio_path = tmp_path / "scene.mp3"
    subtitle_path = tmp_path / "scene.srt"

    asyncio.run(
        voice_generator._generate_scene_voiceover(
            "महादेव", str(audio_path), str(subtitle_path)
        )
    )

    assert audio_path.read_bytes() == b"audio"
    assert "महादेव" in subtitle_path.read_text(encoding="utf-8")


def test_visual_generator_falls_back_for_payment_required(tmp_path, monkeypatch):
    import requests
    from PIL import Image
    from modules import visual_generator

    response = requests.Response()
    response.status_code = 402
    monkeypatch.setattr(visual_generator.requests, "get", lambda *args, **kwargs: response)
    output_path = tmp_path / "fallback.jpg"

    visual_generator.generate_visual_for_scene(
        "ancient temple india", str(output_path), "short"
    )

    with Image.open(output_path) as image:
        assert image.size == (1080, 1920)
        assert image.format == "JPEG"


def test_visual_generator_exposes_scene_visual_entrypoint(tmp_path, monkeypatch):
    from modules import visual_generator

    monkeypatch.setattr(
        visual_generator,
        "generate_visual_for_scene",
        lambda prompt, path, video_type: path,
    )
    paths = visual_generator.fetch_scene_visuals(
        [
            {"visual_query_en": "mountain temple"},
            {"narration": "महादेव का रहस्य"},
        ],
        "short",
        str(tmp_path / "scenes"),
    )

    assert paths == [
        str(tmp_path / "scenes" / "scene_001.jpg"),
        str(tmp_path / "scenes" / "scene_002.jpg"),
    ]


def test_subtitle_filter_path_is_absolute_and_escaped():
    from modules.video_generator import _escape_subtitle_path

    escaped = _escape_subtitle_path(r"C:\video files\subs.srt")
    quoted = _escape_subtitle_path("/tmp/captions,it's:ok.srt")

    assert escaped.startswith("/")
    assert "C\\:" in escaped
    assert "video files/subs.srt" in escaped
    assert quoted == "/tmp/captions\\,it\\'s\\:ok.srt"


def test_renderer_uses_scene_durations_and_escaped_subtitles(tmp_path, monkeypatch):
    from modules import video_generator

    monkeypatch.setattr(video_generator, "get_audio_duration", lambda path: 1.0)
    image_paths = [tmp_path / "one.jpg", tmp_path / "two.jpg"]
    for path in image_paths:
        path.write_bytes(b"image")
    subtitle_path = tmp_path / "captions.srt"
    subtitle_path.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nहर हर महादेव\n", encoding="utf-8"
    )
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        if command[0] == "ffmpeg":
            with open(command[-1], "wb") as output:
                output.write(b"video")

    monkeypatch.setattr(video_generator.subprocess, "run", fake_run)
    output_path = tmp_path / "final.mp4"

    result = video_generator.render_video(
        [str(path) for path in image_paths],
        str(tmp_path / "audio.mp3"),
        str(subtitle_path),
        str(output_path),
        scene_durations=[0.4, 0.6],
    )

    clip_commands = [command for command in commands if "_clip_" in command[-1]]
    assert [command[command.index("-frames:v") + 1] for command in clip_commands] == [
        "10", "15"
    ]
    final_command = commands[-1]
    filter_graph = final_command[final_command.index("-filter_complex") + 1]
    assert "subtitles='/tmp/ffmpeg-subs-" in filter_graph
    assert "/subtitles.srt" in filter_graph
    assert result == str(output_path.resolve())
    assert output_path.exists()


def test_real_ffmpeg_render_with_special_subtitle_path(tmp_path, monkeypatch):
    import shutil
    import subprocess
    import pytest
    from PIL import Image
    from modules import video_generator

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("FFmpeg is required for the render integration test.")

    audio_path = tmp_path / "audio.wav"
    subprocess.run(
        [
            ffmpeg, "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-c:a", "pcm_s16le", str(audio_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    image_path = tmp_path / "scene.jpg"
    Image.new("RGB", (1080, 1920), (30, 45, 60)).save(image_path)
    subtitle_path = tmp_path / "captions,it's:ok.srt"
    subtitle_path.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nsubtitle path integration\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(video_generator, "get_audio_duration", lambda path: 1.0)
    output_path = tmp_path / "rendered.mp4"

    video_generator.render_video(
        [str(image_path)],
        str(audio_path),
        str(subtitle_path),
        str(output_path),
        scene_durations=[1.0],
    )

    subprocess.run(
        [ffmpeg, "-v", "error", "-i", str(output_path), "-f", "null", "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert output_path.stat().st_size > 0


def test_short_dry_run_orchestrates_all_pipeline_stages(tmp_path, monkeypatch):
    import main

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main, "load_dotenv", lambda: None)
    monkeypatch.setattr(main, "init_db", lambda: None)
    monkeypatch.setattr(
        main,
        "select_unique_topic",
        lambda video_type: {"topic": "परीक्षण विषय", "research_summary": "शोध"},
    )
    scenes = [{"narration": "हर हर महादेव", "visual_query_en": "temple"}]
    monkeypatch.setattr(
        main,
        "generate_script",
        lambda topic, video_type: {
            "scenes": scenes,
            "full_narration": "हर हर महादेव",
            "hook": "एक रहस्य",
        },
    )
    monkeypatch.setattr(
        main,
        "generate_voiceover",
        lambda text, audio, subtitles, scenes: [1.0],
    )
    monkeypatch.setattr(main, "fetch_scene_visuals", lambda *args: ["scene.jpg"])

    def render(images, audio, subtitles, output, video_type, scene_durations):
        with open(output, "wb") as video:
            video.write(b"video")

    monkeypatch.setattr(main, "render_video", render)
    monkeypatch.setattr(main, "create_thumbnail", lambda *args: "thumbnail.jpg")
    monkeypatch.setattr(
        main,
        "generate_seo_metadata",
        lambda *args: {"title": "शीर्षक", "description": "विवरण"},
    )
    monkeypatch.setattr(
        main,
        "verify_video_quality",
        lambda *args: (True, "passed"),
    )
    notifications = []
    monkeypatch.setattr(main, "notify", lambda message, is_error=False: notifications.append(message))

    main.run_pipeline("short", dry_run=True)

    assert (tmp_path / "output/final_short.mp4").exists()
    assert any("Dry run completed successfully" in message for message in notifications)


def test_quality_check_rejects_audio_video_drift(tmp_path, monkeypatch):
    from modules.quality_checker import verify_video_quality

    video = tmp_path / "video.mp4"
    video.write_bytes(b"x" * 50_000)
    probe = {
        "streams": [
            {"codec_type": "video", "width": 1080, "height": 1920, "duration": "45.0"},
            {"codec_type": "audio", "duration": "44.5"},
        ],
        "format": {"duration": "45.0"},
    }
    monkeypatch.setattr(
        "modules.quality_checker.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=json.dumps(probe)),
    )

    passed, message = verify_video_quality(
        str(video), "short", {"title": "शीर्षक", "description": "विवरण"}
    )

    assert not passed
    assert "out of sync" in message
