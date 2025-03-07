import streamlit as st
import edge_tts
import asyncio
import os
from io import BytesIO
import re

# 异步函数：将文本转换为语音
async def text_to_speech(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    return output_file

# 解析 SRT 内容并提取纯文本
def parse_srt(srt_content):
    # 分割成每个字幕块
    blocks = re.split(r'\n\n', srt_content.strip())
    subtitles = []
    
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:  # 确保有编号、时间和文本
            text = ' '.join(lines[2:])  # 合并多行文本
            subtitles.append(text)
    
    return subtitles

# 主程序
def main():
    st.title("SRT 字幕转语音工具")
    st.write("请粘贴 SRT 字幕内容，选择音色，然后生成 MP3 文件")

    # 音色选项（具体名称）
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
                # 解析 SRT 内容
                subtitles = parse_srt(srt_content)
                full_text = " ".join(subtitles)
                
                # 生成临时文件名
                output_file = "output.mp3"
                
                # 运行异步 TTS 转换
                try:
                    asyncio.run(text_to_speech(full_text, voice_code, output_file))
                    
                    # 提供下载链接
                    with open(output_file, "rb") as file:
                        st.audio(file, format="audio/mp3")
                        st.download_button(
                            label="下载 MP3 文件",
                            data=file,
                            file_name="subtitle_audio.mp3",
                            mime="audio/mp3"
                        )
                    
                    # 清理临时文件
                    os.remove(output_file)
                    
                except Exception as e:
                    st.error(f"生成语音时出错: {str(e)}")
        else:
            st.warning("请先输入 SRT 字幕内容！")

if __name__ == "__main__":
    main()
