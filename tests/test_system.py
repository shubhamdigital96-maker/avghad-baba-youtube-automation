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


def test_scene_subtitles_are_shifted_by_prior_audio_duration(tmp_path):
    from modules.voice_generator import _combine_subtitles

    first = tmp_path / "first.srt"
    second = tmp_path / "second.srt"
    combined = tmp_path / "combined.srt"
    first.write_text("1\n00:00:00,000 --> 00:00:00,500\nपहला दृश्य\n", encoding="utf-8")
    second.write_text("1\n00:00:00,100 --> 00:00:00,600\nदूसरा दृश्य\n", encoding="utf-8")

    _combine_subtitles([str(first), str(second)], [1.25, 1.5], str(combined))

    assert "2\n00:00:01,350 --> 00:00:01,850\nदूसरा दृश्य" in combined.read_text(encoding="utf-8")


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
