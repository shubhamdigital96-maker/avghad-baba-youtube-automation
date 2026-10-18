import os
import subprocess
import json
import math
import shutil
import tempfile


def _allocate_scene_frames(scene_durations: list, total_audio_duration: float, fps: int = 25) -> list:
    if (
        not scene_durations
        or not math.isfinite(total_audio_duration)
        or total_audio_duration <= 0
        or fps <= 0
        or any(not math.isfinite(d) or d <= 0 for d in scene_durations)
    ):
        raise ValueError("Invalid positive audio duration or scene durations")

    total_target_frames = math.ceil(total_audio_duration * fps)
    if total_target_frames < len(scene_durations):
        raise ValueError("Audio duration is too short to allocate at least one frame per scene.")
    total_scene_dur = sum(scene_durations)
    if total_scene_dur <= 0:
        raise ValueError("Total scene duration must be positive")

    exact_allocations = [
        total_target_frames * duration / total_scene_dur
        for duration in scene_durations
    ]
    frames = [max(1, math.floor(allocation)) for allocation in exact_allocations]
    remainder = total_target_frames - sum(frames)
    remainder_order = sorted(
        range(len(frames)),
        key=lambda index: exact_allocations[index] - math.floor(exact_allocations[index]),
        reverse=True,
    )
    if remainder > 0:
        for index in remainder_order[:remainder]:
            frames[index] += 1
    elif remainder < 0:
        while remainder < 0:
            index = max(
                (index for index, count in enumerate(frames) if count > 1),
                key=lambda candidate: frames[candidate],
            )
            frames[index] -= 1
            remainder += 1
    return frames


def get_audio_duration(audio_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", os.path.abspath(audio_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(json.loads(res.stdout)["format"]["duration"])


def _escape_subtitle_path(path: str) -> str:
    return (
        os.path.abspath(path)
        .replace("\\", "/")
        .replace(":", "\\:")
        .replace(",", "\\,")
        .replace("'", "\\'")
        .replace('"', '\\"')
    )


def _ffconcat_quote(path: str) -> str:
    return "'" + os.path.abspath(path).replace("'", "'\\''") + "'"


def render_video(
    image_paths: list,
    audio_path: str,
    subs_path: str,
    out_mp4: str,
    video_type: str = "short",
    scene_durations: list | None = None,
) -> str:
    if not image_paths:
        raise ValueError("At least one scene image is required.")

    w, h = (1080, 1920) if video_type == "short" else (1920, 1080)
    audio_path = os.path.abspath(audio_path)
    out_mp4 = os.path.abspath(out_mp4)
    os.makedirs(os.path.dirname(out_mp4), exist_ok=True)
    image_paths = [os.path.abspath(path) for path in image_paths]
    total_dur = get_audio_duration(audio_path)
    if scene_durations is None:
        scene_durations = [total_dur / len(image_paths)] * len(image_paths)
    if len(scene_durations) != len(image_paths):
        raise ValueError("Each scene image must have a matching audio duration.")
    scene_frames = _allocate_scene_frames(scene_durations, total_dur)

    abs_subs_path = os.path.abspath(subs_path)
    if not os.path.exists(abs_subs_path) or os.path.getsize(abs_subs_path) == 0:
        raise FileNotFoundError(f"Subtitle file is missing or empty: {abs_subs_path}")

    temp_clips = []
    concat_list = f"{out_mp4}_list.txt"
    merged_video = f"{out_mp4}_merged.mp4"
    subtitle_temp_dir = tempfile.TemporaryDirectory(prefix="ffmpeg-subs-")
    safe_subs_path = os.path.join(subtitle_temp_dir.name, "subtitles.srt")
    try:
        shutil.copyfile(abs_subs_path, safe_subs_path)
        for idx, (img, frames) in enumerate(zip(image_paths, scene_frames)):
            clip_path = f"{out_mp4}_clip_{idx}.mp4"
            vf = (
                f"scale={w * 2}:{h * 2},"
                f"zoompan=z='min(zoom+0.001,1.2)':x='iw/2-(iw/zoom/2)':"
                f"y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps=25,"
                "format=yuv420p"
            )
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", img,
                "-vf", vf, "-frames:v", str(frames),
                "-r", "25", "-c:v", "libx264", "-preset", "veryfast",
                "-pix_fmt", "yuv420p", clip_path,
            ]
            temp_clips.append(clip_path)
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        with open(concat_list, "w", encoding="utf-8") as concat_file:
            for clip_path in temp_clips:
                concat_file.write(f"file {_ffconcat_quote(clip_path)}\n")

        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i",
                concat_list, "-c", "copy", merged_video,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        formatted_subs = _escape_subtitle_path(safe_subs_path)
        sub_style = (
            "FontName=Noto Sans Devanagari,FontSize=22,PrimaryColour=&H0000FFFF,"
            "OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=3,"
            "Outline=2,Shadow=1,Alignment=2"
        )
        vf_sub = f"subtitles='{formatted_subs}':force_style='{sub_style}'"
        final_cmd = [
            "ffmpeg", "-y", "-i", merged_video, "-i", audio_path,
            "-f", "lavfi", "-i", f"sine=frequency=136.1:duration={total_dur:.2f}",
            "-filter_complex",
            f"[0:v]{vf_sub}[v];[2:a]volume=0.03[bg];"
            "[1:a][bg]amix=inputs=2:duration=first[aout]",
            "-map", "[v]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "22",
            "-c:a", "aac", "-b:a", "192k", "-shortest", out_mp4,
        ]
        subprocess.run(final_cmd, check=True)
    finally:
        subtitle_temp_dir.cleanup()
        for path in temp_clips + [concat_list, merged_video]:
            if os.path.exists(path):
                os.remove(path)
    return out_mp4
