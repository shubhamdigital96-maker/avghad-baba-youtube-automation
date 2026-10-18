import os
import asyncio
import edge_tts

def _combine_subtitles(srt_files: list, offsets: list, output_path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    combined_content = "1\n00:00:00,000 --> 00:00:05,000\nAvghad Baba India\n\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(combined_content)
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
