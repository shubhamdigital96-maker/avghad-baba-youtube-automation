import os
import asyncio
import subprocess
import tempfile
import edge_tts
from datetime import timedelta


def _parse_srt_time(time_str: str) -> timedelta:
    time_str = time_str.replace(',', '.')
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    sec_parts = parts[2].split('.')
    seconds = int(sec_parts[0])
    milliseconds = int(sec_parts[1]) if len(sec_parts) > 1 else 0
    return timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)

def _format_srt_time(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    milliseconds = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def _combine_subtitles(srt_files: list, offsets: list, output_path: str) -> str:
    output_path = os.path.abspath(output_path)
    srt_files = [os.path.abspath(path) for path in srt_files]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    combined_blocks = []
    counter = 1
    cumulative_offset = timedelta(0)

    for i, srt_file in enumerate(srt_files):
        if not os.path.exists(srt_file):
            if i < len(offsets):
                cumulative_offset += timedelta(seconds=offsets[i])
            continue
        with open(srt_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        
        if content:
            blocks = content.split('\n\n')
            for block in blocks:
                lines = block.split('\n')
                if len(lines) >= 3:
                    times = lines[1].split(' --> ')
                    if len(times) == 2:
                        start_td = _parse_srt_time(times[0]) + cumulative_offset
                        end_td = _parse_srt_time(times[1]) + cumulative_offset
                        new_time_line = f"{_format_srt_time(start_td)} --> {_format_srt_time(end_td)}"
                        text = '\n'.join(lines[2:])
                        combined_blocks.append(f"{counter}\n{new_time_line}\n{text}")
                        counter += 1
                        
        if i < len(offsets):
            cumulative_offset += timedelta(seconds=offsets[i])

    final_content = '\n\n'.join(combined_blocks) + ('\n' if combined_blocks else '')
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_content)
    return output_path


async def _generate_scene_voiceover(text: str, output_audio: str, output_srt: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_audio)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(output_srt)), exist_ok=True)

    communicate = edge_tts.Communicate(
        text,
        "hi-IN-SwaraNeural",
        boundary="WordBoundary",
    )
    submaker = edge_tts.SubMaker()

    with open(os.path.abspath(output_audio), "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)

    subtitles = submaker.get_srt()
    if not subtitles.strip():
        raise RuntimeError("Edge TTS returned no word-boundary subtitle data.")
    with open(os.path.abspath(output_srt), "w", encoding="utf-8") as f:
        f.write(subtitles)


def _get_audio_duration(audio_path: str) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", os.path.abspath(audio_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    duration = float(result.stdout.strip())
    if duration <= 0:
        raise ValueError(f"Audio has invalid duration: {audio_path}")
    return duration


def _ffconcat_quote(path: str) -> str:
    return "'" + os.path.abspath(path).replace("'", "'\\''") + "'"


async def generate_voiceover_async(text: str, output_audio: str, output_srt: str, scenes=None):
    scene_texts = []
    for scene in scenes or []:
        if not isinstance(scene, dict) or not isinstance(scene.get("narration"), str):
            raise ValueError("Every narration scene must contain a text narration.")
        scene_text = scene["narration"].strip()
        if not scene_text:
            raise ValueError("Every narration scene must contain a text narration.")
        scene_texts.append(scene_text)
    if scenes is None or not scene_texts:
        scene_texts = [text.strip()]
    if not scene_texts[0] and len(scene_texts) == 1:
        raise ValueError("Narration text cannot be empty.")

    output_audio = os.path.abspath(output_audio)
    output_srt = os.path.abspath(output_srt)
    os.makedirs(os.path.dirname(output_audio), exist_ok=True)
    os.makedirs(os.path.dirname(output_srt), exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="voice-scenes-", dir=os.path.dirname(output_audio)) as temp_dir:
        scene_audio = []
        scene_subtitles = []
        scene_durations = []

        for index, scene_text in enumerate(scene_texts):
            scene_audio_path = os.path.join(temp_dir, f"scene_{index:03d}.mp3")
            scene_srt_path = os.path.join(temp_dir, f"scene_{index:03d}.srt")
            await _generate_scene_voiceover(scene_text, scene_audio_path, scene_srt_path)
            scene_audio.append(scene_audio_path)
            scene_subtitles.append(scene_srt_path)
            scene_durations.append(await asyncio.to_thread(_get_audio_duration, scene_audio_path))

        concat_path = os.path.join(temp_dir, "scenes.txt")
        with open(concat_path, "w", encoding="utf-8") as concat_file:
            for scene_path in scene_audio:
                concat_file.write(f"file {_ffconcat_quote(scene_path)}\n")

        await asyncio.to_thread(
            subprocess.run,
            [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_path,
                "-c", "copy", output_audio,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _combine_subtitles(scene_subtitles, scene_durations, output_srt)

    return scene_durations


def generate_voiceover(text: str, output_audio: str, output_srt: str, scenes=None, **kwargs):
    return asyncio.run(generate_voiceover_async(text, output_audio, output_srt, scenes=scenes))
