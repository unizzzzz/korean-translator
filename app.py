import streamlit as st
import google.generativeai as genai
from deep_translator import GoogleTranslator
from gtts import gTTS
import os
# 新增語音辨識套件
from streamlit_mic_recorder import speech_to_text

st.set_page_config(page_title="AI 雙向翻譯小幫手", page_icon="🇰🇷", layout="wide")

# === 【重要】請將你的 Gemini API Key 填入下方的引號中 ===
GEMINI_API_KEY = "AIzaSyA6dBnvm1niPkh58MTaMpcOW9lPy0HDq54"

if "history" not in st.session_state:
    st.session_state.history = []
if "current_view" not in st.session_state:
    st.session_state.current_view = None

with st.sidebar:
    st.header("⚙️ 引擎設定")
    # 【改動1】改成單純的選擇欄位，不再顯示 API 輸入框
    engine_choice = st.radio("選擇翻譯引擎：", ["高級翻譯 (AI)", "一般 GOOGLE 翻譯"])
    
    st.divider()
    st.header("🕒 歷史紀錄")
    
    if st.button("🗑️ 清除所有"):
        st.session_state.history = []
        st.session_state.current_view = None
        st.rerun()

    st.write("---")
    for i, item in enumerate(reversed(st.session_state.history)):
        real_idx = len(st.session_state.history) - 1 - i
        preview_text = item['source_text'][:8] + ("..." if len(item['source_text']) > 8 else "")
        
        colA, colB = st.columns([4, 1])
        with colA:
            if st.button(f"📄 {preview_text}", key=f"view_{real_idx}"):
                st.session_state.current_view = item
        with colB:
            if st.button("❌", key=f"del_{real_idx}"):
                st.session_state.history.pop(real_idx)
                if st.session_state.current_view == item:
                    st.session_state.current_view = None
                st.rerun()

def translate_with_ai(text, direction, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    if direction == "韓文 ➡️ 中文":
        prompt = f"你是一個專業的韓文翻譯。請將以下韓文翻譯成流暢的台灣繁體中文，保留原文語氣。請直接輸出結果：\n{text}"
    else:
        prompt = f"你是一個精通韓文的台灣人。請將以下中文翻譯成自然道地的韓文。這是要在見面會上說的話，請使用適當的敬語。請直接輸出結果：\n{text}"
        
    response = model.generate_content(prompt)
    return response.text.strip()

st.title("🇰🇷 翻譯神器")

direction = st.radio("請選擇方向：", ["韓文 ➡️ 中文", "中文 ➡️ 韓文"], horizontal=True)

if direction == "韓文 ➡️ 中文":
    src_lang, tgt_lang = 'ko', 'zh-TW'
    stt_lang = 'ko-KR'  # 語音辨識設定為韓文
else:
    src_lang, tgt_lang = 'zh-TW', 'ko'
    stt_lang = 'zh-TW'  # 語音辨識設定為中文

# 【改動2】獨立的麥克風語音輸入按鈕
st.write("🎤 **語音輸入：**")
# 這裡會產生一個按鈕，點擊後會啟動瀏覽器的麥克風
spoken_text = speech_to_text(
    language=stt_lang,
    start_prompt="點擊開始錄音",
    stop_prompt="點擊停止錄音",
    just_once=True,
    key=f"stt_{direction}" # 避免切換語言方向時狀態衝突
)

# 如果有講話，自動把講出的文字填入下方輸入框；如果沒講話，就保持原樣
default_text = spoken_text if spoken_text else ""
text_to_translate = st.text_area("或手動修改/輸入文字：", value=default_text, height=120)

if st.button("🚀 開始翻譯", type="primary"):
    if text_to_translate:
        try:
            # 根據側邊欄的選擇，決定要用哪個引擎
            if engine_choice == "高級翻譯 (AI)":
                with st.spinner('AI 正在思考最道地的語氣...'):
                    translated = translate_with_ai(text_to_translate, direction, GEMINI_API_KEY)
                engine_used = "Gemini AI"
            else:
                with st.spinner('使用一般 Google 翻譯...'):
                    translator = GoogleTranslator(source=src_lang, target=tgt_lang)
                    translated = translator.translate(text_to_translate)
                engine_used = "一般 Google 翻譯"
            
            new_record = {
                'direction': direction,
                'source_lang': src_lang,
                'target_lang': tgt_lang,
                'source_text': text_to_translate,
                'translated_text': translated,
                'engine': engine_used
            }
            
            st.session_state.history.append(new_record)
            st.session_state.current_view = new_record
            st.rerun()
            
        except Exception as e:
            st.error(f"發生錯誤：請檢查 API 金鑰是否填寫正確 ({e})")
    else:
        st.warning("請先輸入文字內容。")

st.divider()

if st.session_state.current_view:
    view = st.session_state.current_view
    
    st.caption(f"模式：{view['direction']} | 引擎：{view['engine']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**原文**")
        st.write(view['source_text'])
        if st.button("🔊 發音", key="btn_src"):
            tts_src = gTTS(text=view['source_text'], lang=view['source_lang'])
            tts_src.save("src.mp3")
            st.audio("src.mp3", format='audio/mp3')

    with col2:
        st.markdown("**翻譯結果**")
        st.markdown(f"""
            <div style='font-size: 26px; font-weight: bold; color: #1E90FF; line-height: 1.4; padding: 10px; border-left: 5px solid #1E90FF; background-color: #f0f8ff;'>
                {view['translated_text']}
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔊 發音", key="btn_tgt"):
            tts_tgt = gTTS(text=view['translated_text'], lang=view['target_lang'])
            tts_tgt.save("tgt.mp3")
            st.audio("tgt.mp3", format='audio/mp3')
