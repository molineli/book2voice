import streamlit as st
import os
import shutil
import asyncio
from src.book_loader import BookLoader
from src.ai_director import AIDirector
from src.audio_engine import AudioEngine
from src.config import configure_ffmpeg
from src.utils import clear_temp_folder
from pydub import AudioSegment

# 初始化
configure_ffmpeg()


def merge_audio_files(file_paths, output_path):
    combined = AudioSegment.empty()
    progress_bar = st.progress(0)
    status = st.empty()

    total = len(file_paths)
    for i, f in enumerate(file_paths):
        if f and os.path.exists(f):
            try:
                combined += AudioSegment.from_mp3(f)
            except Exception:
                pass
        if i % 5 == 0:
            status.text(f"正在拼接: {i}/{total}")
            progress_bar.progress((i + 1) / total)

    combined.export(output_path, format="mp3")
    status.text("拼接完成！")
    return output_path


# --- 核心异步逻辑：封装整个生成过程 ---
async def process_generation(chapters, selected_indices, use_ai, director, ai_concurrency):
    """
    将章节遍历和音频生成逻辑封装在同一个 Async Loop 中，
    确保 AudioEngine 的 Semaphore 与当前 Loop 绑定。
    """
    # 在 Loop 内部初始化 Engine，防止 Semaphore 报错
    engine = AudioEngine()
    final_audio_files = []

    total_chapters = len(selected_indices)
    global_progress = st.progress(0)
    status_text = st.empty()

    # 创建 AI 并发限制信号量
    ai_semaphore = asyncio.Semaphore(ai_concurrency)

    # 内部辅助函数：并发执行 AI 标注
    async def process_ai_segment(segment):
        async with ai_semaphore:
            # 将同步的 director.direct_scene 放入线程池执行，避免阻塞事件循环
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, director.direct_scene, segment)

    for idx, chap_idx in enumerate(selected_indices):
        chapter = chapters[chap_idx]
        status_text.markdown(f"### 正在处理: **{chapter.title}** ({idx + 1}/{total_chapters})")

        # 1. 文本切分
        raw_text = chapter.content
        text_segments = [raw_text[i:i + 800] for i in range(0, len(raw_text), 800)]

        chapter_scripts = []
        chapter_progress = st.progress(0)

        # === 阶段 A: AI 剧本标注 (并发加速) ===
        if use_ai:
            status_text.markdown(f"### 🧠 AI 导演正在分析剧本 (并发数: {ai_concurrency})...")

            # 创建所有分段的 AI 任务
            ai_tasks = [process_ai_segment(seg) for seg in text_segments]

            # 执行并发并等待结果 (保持顺序)
            # 为了显示进度，我们可以使用 as_completed，但为了保持顺序，直接 gather 更简单
            # 如果需要进度条，可以简单地分批或者直接等待
            chapter_scripts = await asyncio.gather(*ai_tasks)

            # 简单的 AI 完成进度更新
            chapter_progress.progress(0.3)  # 假设 AI 占 30% 进度
        else:
            # 普通模式：直接构造默认脚本
            chapter_scripts = [[{"text": seg, "role": "narrator", "params": {}}] for seg in text_segments]
            chapter_progress.progress(0.1)

        # === 阶段 B: 音频生成 (并发 TTS) ===
        status_text.markdown(f"### 🎙️ 正在录制音频 ({chapter.title})...")
        chapter_audio_segments = []

        # 遍历每个段落的脚本进行 TTS
        total_segments = len(text_segments)
        for seg_i, script in enumerate(chapter_scripts):
            tasks = []
            for script_idx, item in enumerate(script):
                unique_id = (idx * 10000) + (seg_i * 100) + script_idx
                tasks.append(engine.generate_segment(item, unique_id))

            if tasks:
                segment_files = await asyncio.gather(*tasks)
                chapter_audio_segments.extend([f for f in segment_files if f])

            # 更新章节进度 (从 30% 到 100%)
            current_progress = 0.3 + (0.7 * (seg_i + 1) / total_segments)
            chapter_progress.progress(min(current_progress, 1.0))

        final_audio_files.extend(chapter_audio_segments)
        global_progress.progress((idx + 1) / total_chapters)

    return final_audio_files


def main():
    st.set_page_config(page_title="AI 有声剧工坊", layout="wide", page_icon="🎭")

    st.title("🎭 AI 智能有声剧制作工坊")
    st.markdown("支持 **PDF/EPUB/DOCX** · **大模型导演模式** · **多角色演绎**")

    # --- 侧边栏配置 ---
    with st.sidebar:
        st.header("⚙️ 全局设置")

        # API 配置
        api_key = st.text_input("LLM API Key", type="password", help="DeepSeek 或 Qwen 的 API Key")
        base_url = st.text_input("Base URL", value="https://api.deepseek.com", help="例如: https://api.deepseek.com")
        model_name = st.text_input("模型名称", value="deepseek-chat")
        output_name = st.text_input("输出文件名", value="final_book")

        use_ai = st.toggle("启用 AI 导演模式", value=True, help="开启后将使用 LLM 分析情感和角色。")

        if use_ai:
            st.markdown("---")
            st.markdown("**🚀 加速设置**")
            ai_concurrency = st.slider(
                "AI 思考并发数",
                min_value=1,
                max_value=20,
                value=5,
                help="DeepSeek 不限制并发，调高此数值可大幅加快剧本分析速度。建议 5-10。"
            )
        else:
            ai_concurrency = 1  # 不用 AI 时此值无效

        if not api_key and use_ai:
            st.warning("启用 AI 模式需要填写 API Key")

    # --- 1. 文件上传与解析 ---
    if "book_chapters" not in st.session_state:
        st.session_state.book_chapters = None

    uploaded_file = st.file_uploader("📂 拖入书籍文件", type=["epub", "docx", "pdf", "txt"])

    if uploaded_file and st.session_state.book_chapters is None:
        with st.spinner("正在解析书籍结构..."):
            try:
                chapters = BookLoader.load_book(uploaded_file)
                st.session_state.book_chapters = chapters
                st.success(f"解析成功！共识别到 {len(chapters)} 个章节")
                st.rerun()  # 刷新以显示章节选择
            except Exception as e:
                st.error(f"解析失败: {e}")

    # --- 2. 章节选择与生成 ---
    if st.session_state.book_chapters:
        chapters = st.session_state.book_chapters
        chapter_titles = [f"{i + 1}. {c.title}" for i, c in enumerate(chapters)]

        selected_indices = st.multiselect(
            "📜 请选择要生成的章节 (支持多选)",
            options=list(range(len(chapters))),
            format_func=lambda x: chapter_titles[x]
        )

        if st.button("🎬 开始制作有声剧") and selected_indices:
            if use_ai and not api_key:
                st.error("请先在侧边栏配置 API Key")
                st.stop()

            # 准备工作
            director = AIDirector(api_key, base_url, model_name) if use_ai else None

            # --- 主处理循环 ---
            try:
                final_audio_files = asyncio.run(
                    process_generation(chapters, selected_indices, use_ai, director, ai_concurrency)
                )
            except Exception as e:
                st.error(f"生成过程中发生错误: {e}")
                # 打印完整堆栈方便调试
                import traceback
                st.code(traceback.format_exc())
                st.stop()

            # --- 3. 最终合并 ---
            if final_audio_files:
                st.text("正在合成最终母带 (Rendering)...")
                output_filename = output_name + '.mp3'
                final_path = merge_audio_files(final_audio_files, output_filename)

                st.success("✨ 制作完成！")
                st.audio(final_path)
                with open(final_path, "rb") as f:
                    st.download_button("⬇️ 下载有声剧", f, file_name=output_filename)
            else:
                st.warning("未能生成任何音频，请检查文本内容。")

    clear_temp_folder()


if __name__ == "__main__":
    main()
