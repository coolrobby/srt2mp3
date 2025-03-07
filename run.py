import streamlit as st
import edge_tts
import asyncio
import os
from io import BytesIO
import re
from pydub import AudioSegment
from datetime import datetime

# 异步函数：将文本转换为语音
async def text_to_speech(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    return output_file

# 解析 SRT 内容，返回时间戳和文本
def parse_srt(srt_content):
    blocks = re.split(r'\n\n', srt_content.strip())
    subtitles = []
    
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            # 解析时间戳
            timing = lines[1].split(' --> ')
            start_time = timing[0].replace(',', '.')
            end_time = timing[1].replace(',', '.')
            
            # 计算时长（毫秒）
            start_dt = datetime.strptime(start_time, '%H:%M:%S.%f')
            end_dt = datetime.strptime(end_time, '%H:%M:%S.%f')
            duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
            
            # 提取文本
            text = ' '.join(lines[2:])
            subtitles.append({
                'start': start_time,
                'duration_ms': duration_ms,
                'text': text
            })
    
    return subtitles

# 调整音频速度以匹配目标时长
def adjust_audio_speed(audio_file, target_duration_ms):
    audio = AudioSegment.from_mp3(audio_file)
    original_duration_ms = len(audio)
    
    if original_duration_ms > target_duration_ms:
        # 计算加速倍率
        speed_factor = original_duration_ms / target_duration_ms
        # 加速音频
        adjusted_audio = audio.speedup(playback_speed=speed_factor)
        return adjusted_audio
    return audio

# 主程序
def main():
    st.title("SRT 字幕转语音工具（匹配时间轴）")
    st.write("请粘贴 SRT 字幕内容，选择音色，生成与时间轴匹配的 MP3 文件")

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
                # 解析 SRT 内容
                subtitles = parse_srt(srt_content)
                
                # 创建最终音频
                final_audio = AudioSegment.silent(duration=0)
                temp_files = []
                
                try:
                    for i, subtitle in enumerate(subtitles):
                        text = subtitle['text']
                        target_duration_ms = subtitle['duration_ms']
                        start_time = subtitle['start']
                        
                        # 生成临时音频文件
                        temp_file = f"temp_{i}.mp3"
                        asyncio.run(text_to_speech(text, voice_code, temp_file))
                        temp_files.append(temp_file)
                        
                        # 调整音频速度
                        adjusted_audio = adjust_audio_speed(temp_file, target_duration_ms)
                        
                        # 计算起始位置（毫秒）
                        start_dt = datetime.strptime(start_time, '%H:%M:%S.%f')
                        start_ms = int(start_dt.hour * 3600 + start_dt.minute * 60 + start_dt.second) * 1000 + int(start_dt.microsecond / 1000)
                        
                        # 如果 final_audio 时长不足，填充静音
                        if len(final_audio) < start_ms:
                            final_audio = final_audio + AudioSegment.silent(duration=start_ms - len(final_audio))
                        
                        # 叠加音频
                        final_audio = final_audio.overlay(adjusted_audio, position=start_ms)
                    
                    # 导出最终音频
                    output_file = "output.mp3"
                    final_audio.export(output_file, format="mp3")
                    
                    # 提供播放和下载
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
                    for temp_file in temp_files:
                        os.remove(temp_file)
                
                except Exception as e:
                    st.error(f"生成语音时出错: {str(e)}")
        else:
            st.warning("请先输入 SRT 字幕内容！")

if __name__ == "__main__":
    main()
