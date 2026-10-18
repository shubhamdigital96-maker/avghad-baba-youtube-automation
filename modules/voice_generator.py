import os
import asyncio
import edge_tts
from datetime import datetime, timedelta

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
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    combined_blocks = []
    counter = 1

    for srt_file, offset in zip(srt_files, offsets):
        if not os.path.exists(srt_file):
            continue
        with open(srt_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            continue
        
        blocks = content.split('\n\n')
        offset_td = timedelta(seconds=offset)
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                times = lines[1].split(' --> ')
                if len(times) == 2:
                    start_td = _parse_srt_time(times[0]) + offset_td
                    end_td = _parse_srt_time(times[1]) + offset_td
                    new_time_line = f"{_format_srt_time(start_td)} --> {_format_srt_time(end_td)}"
                    text = '\n'.join(lines[2:])
                    combined_blocks.append(f"{counter}\n{new_time_line}\n{text}")
                    counter += 1

    final_content = '\n\n'.join(combined_blocks) + '\n'
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_content)
    return output_path

async def generate_voiceover_async(text: str, output_audio: str, output_srt: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_audio)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(output_srt)), exist_ok=True)

    communicate = edge_tts.Communicate(text, "hi-IN-SwaraNeural")
    submaker = edge_tts.SubMaker()
    
    with open(output_audio, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)

    with open(output_srt, "w", encoding="utf-8") as f:
        f.write(submaker.get_srt())

def generate_voiceover(text: str, output_audio: str, output_srt: str):
    asyncio.run(generate_voiceover_async(text, output_audio, output_srt))
