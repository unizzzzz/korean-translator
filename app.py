import streamlit as st
import google.generativeai as genai
from deep_translator import GoogleTranslator
from gtts import gTTS
import os

st.set_page_config(page_title="AI 雙向翻譯小幫手", page_icon="🇰🇷", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []
if "current_view" not in st.session_state:
    st.session_state.current_view = None

with st.sidebar:
    st.header("⚙️ 引擎設定")
    st.caption("輸入 API 以啟用 AI 潤飾。若留空，將自動使用一般 Google 翻譯。")
    
    # 【功能3：記住 API】將你的 API Key 填入 value 的引號中，以後就不用重貼了
    gemini_key = st.text_input("Gemini API Key", value="AIzaSyA6dBnvm1niPkh58MTaMpcOW9lPy0HDq54", type="password")
    
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
else:
    src_lang, tgt_lang = 'zh-TW', 'ko'

# 【功能2：語音輸入提示】手機點擊框框後，直接用鍵盤的麥克風講話即可
text_to_translate = st.text_area("請輸入文字 (手機可使用鍵盤麥克風直接語音輸入)：", height=120)

if st.button("🚀 開始翻譯", type="primary"):
    if text_to_translate:
        try:
            # 【功能1：自動切換備用翻譯】
            if gemini_key:
                with st.spinner('AI 正在思考最道地的語氣...'):
                    translated = translate_with_ai(text_to_translate, direction, gemini_key)
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
            st.error(f"發生錯誤：{e}")
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
        # 【功能4：放大手機字體】使用 HTML/CSS 讓字體變大、變粗、變明顯
        st.markdown(f"""
            <div style='font-size: 26px; font-weight: bold; color: #1E90FF; line-height: 1.4; padding: 10px; border-left: 5px solid #1E90FF; background-color: #f0f8ff;'>
                {view['translated_text']}
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔊 發音", key="btn_tgt"):
            tts_tgt = gTTS(text=view['translated_text'], lang=view['target_lang'])
            tts_tgt.save("tgt.mp3")
            st.audio("tgt.mp3", format='audio/mp3')
