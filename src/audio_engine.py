import edge_tts
import asyncio
import os

# 角色到 Edge-TTS 声音的映射表
VOICE_MAP = {
    "narrator": "zh-CN-XiaoxiaoNeural",  # 晓晓 (全能，适合旁白)
    "young_male": "zh-CN-YunxiNeural",  # 云希 (适合男主)
    "young_female": "zh-CN-XiaoyiNeural",  # 晓伊 (适合女主，声音较细)
    "old_male": "zh-CN-YunzeNeural",  # 云泽 (深沉，适合长者)
    "old_female": "zh-CN-Liaoning-XiaobeiNeural",  # 这里的选择较少，暂用这个替代或复用晓晓降调
    "boy": "zh-CN-YunjianNeural",  # 云健 (可以用参数调高音调模拟)
    "girl": "zh-CN-XiaoyiNeural",  # 复用晓伊，参数调高
    "villain": "zh-CN-YunzeNeural"  # 复用云泽，降调
}


class AudioEngine:
    def __init__(self, temp_dir="temp_audio_chunks"):
        self.temp_dir = temp_dir
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        # 信号量控制并发
        self.semaphore = asyncio.Semaphore(5)

    async def generate_segment(self, segment_data, index):
        """
        根据 Script Segment 生成音频
        segment_data: {"text":..., "role":..., "params": {...}}
        """
        role = segment_data.get("role", "narrator")
        text = segment_data.get("text", "")
        params = segment_data.get("params", {})

        if not text.strip():
            return None

        # 1. 确定 Voice
        voice = VOICE_MAP.get(role, VOICE_MAP["narrator"])

        # 2. 组装参数
        rate = params.get("rate", "+0%")
        pitch = params.get("pitch", "+0Hz")
        volume = params.get("volume", "+0%")

        # 3. 生成文件名 (保证顺序)
        output_file = os.path.join(self.temp_dir, f"seg_{index:05d}.mp3")

        async with self.semaphore:
            try:
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=voice,
                    rate=rate,
                    pitch=pitch,
                    volume=volume
                )
                await communicate.save(output_file)
                return output_file
            except Exception as e:
                print(f"TTS Error on seg {index}: {e}")
                return None
