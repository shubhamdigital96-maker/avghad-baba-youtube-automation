import os
import subprocess
import json

def _allocate_scene_frames(scene_durations: list, total_audio_duration: float, fps: int = 25) -> list:
    if not scene_durations or total_audio_duration <= 0 or any(d <= 0 for d in scene_durations):
        raise ValueError("Invalid positive audio duration or scene durations")
    
    total_scene_dur = sum(scene_durations)
    if total_scene_dur <= 0:
        raise ValueError("Total scene duration must be positive")
    
    frames = []
    allocated = 0
    total_target_frames = int(round(total_audio_duration * fps))
    
    for i, d in enumerate(scene_durations):
        if i == len(scene_durations) - 1:
            f = total_target_frames - allocated
        else:
            f = int(round((d / total_scene_dur) * total_target_frames))
        frames.append(max(1, f))
        allocated += frames[-1]
        
    return frames

def get_audio_duration(audio_path: str) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", audio_path]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(json.loads(res.stdout)["format"]["duration"])

def render_video(image_paths: list, audio_path: str, subs_path: str, out_mp4: str, video_type: str = "short") -> str:
    w, h = (1080, 1920) if video_type == "short" else (1920, 1080)
    total_dur = get_audio_duration(audio_path)
    scene_dur = max(2.0, total_dur / max(1, len(image_paths)))

    abs_subs_path = os.path.abspath(subs_path)
    if not os.path.exists(abs_subs_path) or os.path.getsize(abs_subs_path) == 0:
        os.makedirs(os.path.dirname(abs_subs_path), exist_ok=True)
        with open(abs_subs_path, "w", encoding="utf-8") as f:
            f.write("1\n00:00:00,000 --> 00:00:05,000\nAvghad Baba India\n\n")

    temp_clips = []
    for idx, img in enumerate(image_paths):
        clip_path = f"{out_mp4}_clip_{idx}.mp4"
        frames = int(scene_dur * 25)
        vf = (
            f"scale={w*2}:{h*2},"
            f"zoompan=z='min(zoom+0.001,1.2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps=25,"
            f"format=yuv420p"
        )
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", img,
            "-vf", vf, "-t", f"{scene_dur:.2f}",
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", clip_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        temp_clips.append(clip_path)

    concat_list = f"{out_mp4}_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for c in temp_clips:
            f.write(f"file '{os.path.abspath(c)}'\n")

    merged_video = f"{out_mp4}_merged.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", merged_video],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    formatted_subs = abs_subs_path.replace("\\", "/").replace(":", "\\:")
    sub_style = "FontName=Noto Sans Devanagari,FontSize=22,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=3,Outline=2,Shadow=1,Alignment=2"
    vf_sub = f"subtitles='{formatted_subs}':force_style='{sub_style}'"

    final_cmd = [
        "ffmpeg", "-y",
        "-i", merged_video,
        "-i", audio_path,
        "-f", "lavfi", "-i", f"sine=frequency=136.1:duration={total_dur:.2f}",
        "-filter_complex",
        f"[0:v]{vf_sub}[v];[2:a]volume=0.03[bg];[1:a][bg]amix=inputs=2:duration=first[aout]",
        "-map", "[v]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", out_mp4
    ]
    subprocess.run(final_cmd, check=True)

    for c in temp_clips + [concat_list, merged_video]:
        if os.path.exists(c):
            os.remove(c)
    return out_mp4
