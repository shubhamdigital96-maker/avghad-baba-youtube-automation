import asyncio
import edge_tts
import yaml

async def _synthesize(text: str, out_audio: str, out_vtt: str, voice: str, rate: str):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    submaker = edge_tts.SubMaker()
    with open(out_audio, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)
    with open(out_vtt, "w", encoding="utf-8") as vtt_file:
        vtt_file.write(submaker.get_srt())

def generate_voiceover(text: str, out_audio: str, out_subs: str) -> str:
    with open("config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    voice = cfg["voice"]["default"]
    rate = cfg["voice"]["rate"]
    asyncio.run(_synthesize(text, out_audio, out_subs, voice, rate))
    return out_audio
