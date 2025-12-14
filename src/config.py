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
    # 1. 获取项目根目录
    # os.path.dirname(os.path.abspath(__file__)) 是 src 目录
    # os.path.dirname(...) 是项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_dir)

    # 2. 定义可能存放 ffmpeg.exe 的路径 (现在优先搜索根目录)
    possible_paths = [
        base_dir,  # 项目根目录 (推荐位置)
        os.path.join(base_dir, "bin"),  # 项目下的 bin 文件夹
        os.path.join(base_dir, "ffmpeg", "bin")  # 项目下的 ffmpeg/bin 文件夹
    ]

    ffmpeg_bin_dir = None

    for path in possible_paths:
        ffmpeg_exe = os.path.join(path, "ffmpeg.exe")
        ffprobe_exe = os.path.join(path, "ffprobe.exe")

        if os.path.exists(ffmpeg_exe):
            ffmpeg_bin_dir = path
            break

    if ffmpeg_bin_dir:
        # 3. 将路径添加到当前运行时的环境变量 PATH
        # 优先将找到的路径放在最前面，确保系统能优先找到它
        if ffmpeg_bin_dir not in os.environ["PATH"]:
            os.environ["PATH"] = ffmpeg_bin_dir + os.pathsep + os.environ["PATH"]

        print(f"✅ FFmpeg 配置成功。使用的路径: {ffmpeg_bin_dir}")
        print("PATH 环境变量已更新。")

    else:
        # 4. 如果找不到，给出明确警告
        import shutil
        if not shutil.which("ffmpeg"):
            print("❌ 严重警告: 未在系统或项目目录找到 ffmpeg.exe！")
            print(f"请将 ffmpeg.exe 和 ffprobe.exe 放入项目根目录: {base_dir}")
        else:
            print("✅ FFmpeg 存在于系统 PATH 中，但未在项目目录找到。")


# 创建所需的文件夹
def init_directories():
    configure_ffmpeg()  # 初始化时优先配置环境
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
