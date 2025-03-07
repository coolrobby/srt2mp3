import streamlit as st
import edge_tts
import asyncio
import os
from io import BytesIO
import re
import zipfile
import tempfile

# 异步函数：将文本转换为语音
async def text_to_speech(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    return output_file

# 解析 SRT 内容并提取纯文本和序号
def parse_srt(srt_content):
    blocks = re.split(r'\n\n', srt_content.strip())
    subtitles = []
    
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:  # 确保有编号、时间和文本
            number = lines[0]  # 字幕序号
            text = ' '.join(lines[2:])  # 合并多行文本
            subtitles.append((number, text))
    
    return subtitles

# 创建 ZIP 文件
def create_zip(files):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in files:
            file_name = os.path.basename(file_path)
            zip_file.write(file_path, file_name)
    buffer.seek(0)
    return buffer

# 主程序
def main():
    st.title("SRT 字幕转语音工具")
    st.write("请粘贴 SRT 字幕内容，选择音色，然后生成 MP3 文件（包含逐行音频和完整音频）")

    # 音色选项
    voices = {
        "Xiaoxiao (中文大陆女声)": "zh-CN-XiaoxiaoNeural",
        "Yunxi (中文大陆男声)": "zh-CN-YunxiNeural",
        "HsiaoYu (中文台湾女声)": "zh-TW-HsiaoYuNeural",
        "Aria (美式英语女声)": "en-US-AriaNeural",
        "Guy (美式英语男声)": "en-US-GuyNeural",
        "Sonia (英式英语女声)": "en-GB-SoniaNeural",
        "Ryan (英式英语男声)": "en-GB-RyanNeural"
    }
    
    # 输入框
    srt_content = st.text_area("粘贴 SRT 字幕内容", height=300)
    
    # 选择音色
    selected_voice = st.selectbox("选择音色", list(voices.keys()))
    voice_code = voices[selected_voice]
    
    if st.button("生成 MP3"):
        if srt_content:
            with st.spinner("正在处理字幕并生成语音..."):
                try:
                    # 创建临时目录
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # 解析 SRT 内容
                        subtitles = parse_srt(srt_content)
                        full_text = " ".join([text for _, text in subtitles])
                        audio_files = []

                        # 生成完整音频
                        full_audio_file = os.path.join(temp_dir, "full_audio.mp3")
                        asyncio.run(text_to_speech(full_text, voice_code, full_audio_file))
                        audio_files.append(full_audio_file)

                        # 为每行字幕生成单独的音频（只根据文本内容，不考虑时间轴）
                        for number, text in subtitles:
                            output_file = os.path.join(temp_dir, f"subtitle_{number}.mp3")
                            asyncio.run(text_to_speech(text, voice_code, output_file))
                            audio_files.append(output_file)

                        # 播放完整音频
                        with open(full_audio_file, "rb") as file:
                            st.audio(file, format="audio/mp3")

                        # 创建并提供 ZIP 下载
                        zip_buffer = create_zip(audio_files)
                        st.download_button(
                            label="下载所有音频文件 (ZIP)",
                            data=zip_buffer,
                            file_name="subtitle_audios.zip",
                            mime="application/zip"
                        )

                        # 显示每行字幕的音频预览
                        st.write("逐行音频预览：")
                        for number, _ in subtitles:
                            audio_path = os.path.join(temp_dir, f"subtitle_{number}.mp3")
                            with open(audio_path, "rb") as file:
                                st.audio(file, format="audio/mp3")

                except Exception as e:
                    st.error(f"生成语音时出错: {str(e)}")
        else:
            st.warning("请先输入 SRT 字幕内容！")

if __name__ == "__main__":
    main()
