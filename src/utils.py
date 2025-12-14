import shutil
import os
from src.config import TEMP_DIR


def clear_temp_folder():
    """清空临时音频文件夹，防止残留"""
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)


def format_filename(index):
    """生成标准化的临时文件名，保证拼接顺序"""
    return os.path.join(TEMP_DIR, f"chunk_{index:04d}.mp3")
