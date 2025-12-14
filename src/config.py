import os

# 临时文件夹路径
TEMP_DIR = "temp_audio_chunks"
OUTPUT_DIR = "output_audio"

# 默认语音角色
DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"


# FFMPEG 自动配置
def configure_ffmpeg():
    """
    尝试在项目目录下寻找 ffmpeg，并将其添加到环境变量 PATH 中。
    解决用户不会配置系统环境变量的问题。
    """
    # 获取 src/config.py 的上级目录的上级目录 (即项目根目录)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_dir)

    # 定义可能存放 ffmpeg.exe 的路径
    possible_paths = [
        base_dir,  # 项目根目录
        os.path.join(base_dir, "bin"),  # 项目下的 bin 文件夹
        os.path.join(base_dir, "ffmpeg", "bin")  # 项目下的 ffmpeg/bin 文件夹
    ]

    ffmpeg_found = False
    for path in possible_paths:
        ffmpeg_exe = os.path.join(path, "ffmpeg.exe")
        ffprobe_exe = os.path.join(path, "ffprobe.exe")

        # 只要找到了 ffmpeg.exe，就认为该路径有效
        if os.path.exists(ffmpeg_exe):
            print(f"✅ 在项目内发现 FFmpeg: {path}")
            # 将该路径加入当前运行时的环境变量 PATH
            os.environ["PATH"] += os.pathsep + path
            ffmpeg_found = True
            break

    if not ffmpeg_found:
        # 尝试检查系统路径是否已有 ffmpeg (如果不报错则说明系统环境配好了，否则提示警告)
        import shutil
        if not shutil.which("ffmpeg"):
            print("⚠️ 警告: 未在系统路径或项目目录下找到 ffmpeg.exe，音频拼接可能会失败。")
            print("请将 ffmpeg.exe 和 ffprobe.exe 放入项目根目录。")


# 创建所需的文件夹
def init_directories():
    configure_ffmpeg()  # 初始化时优先配置环境
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)