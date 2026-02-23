import streamlit as st
import google.generativeai as genai
from deep_translator import GoogleTranslator
from gtts import gTTS
import os
import re
import io  # 【修復1】新增虛擬記憶體套件，專治 iOS 語音報錯
from streamlit_mic_recorder import speech_to_text

st.set_page_config(page_title="雙向翻譯神器", page_icon="🇰🇷", layout="wide")

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

def is_korean(text):
    if re.search(r'[\uac00-\ud7a3]', text):
        return True
    return False

if "history" not in st.session_state:
    st.session_state.history = []
if "current_view" not in st.session_state:
    st.session_state.current_view = None
if "text_input_area" not in st.session_state:
    st.session_state.text_input_area = ""
if "clear_next_time" not in st.session_state:
    st.session_state.clear_next_time = False

with st.sidebar:
    st.header("⚙️ 引擎設定")
    # 【修復2】加入三種引擎選項，給你「快又準」的選擇
    engine_choice = st.radio("選擇翻譯引擎：", [
        "✨ 高級 AI (最準、較慢)", 
        "⚡ 極速 AI (又快又準)", 
        "🤖 一般 GOOGLE (瞬間、較不準)"
    ])
    
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

# 根據選擇的模型名稱進行翻譯
def translate_with_ai(text, api_key, model_name):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    
    prompt = f"""你是一個精通中韓雙語的專業翻譯人員。
    請自動判斷以下文字的語言：
    1. 如果是「韓文」，請翻譯成流暢自然的「台灣繁體中文」。
    2. 如果是「中文」，請翻譯成自然道地、有禮貌的「韓文敬語」。
    【嚴格指令】只輸出翻譯結果，絕對不要加上任何解釋、羅馬拼音或多餘文字。
    需要翻譯的文字：\n{text}"""
        
    response = model.generate_content(prompt)
    return response.text.strip()

st.title("🇰🇷 雙向翻譯神器")
st.caption("AI 會自動偵測語言：輸入中文翻韓文，輸入韓文翻中文")

st.write("🎤 **語音輸入 (點擊後請說話)：**")

col_mic1, col_mic2 = st.columns(2)
with col_mic1:
    spoken_zh = speech_to_text(
        language='zh-TW',
        start_prompt="🙋‍♂️ 點我說中文",
        stop_prompt="🛑 停止錄音",
        just_once=True,
        key="stt_zh"
    )
with col_mic2:
    spoken_ko = speech_to_text(
        language='ko-KR',
        start_prompt="👩🏻 點我說韓文 (한국어)",
        stop_prompt="🛑 停止錄音",
        just_once=True,
        key="stt_ko"
    )

if spoken_zh:
    st.session_state.text_input_area = spoken_zh
elif spoken_ko:
    st.session_state.text_input_area = spoken_ko

if st.session_state.clear_next_time:
    st.session_state.text_input_area = ""
    st.session_state.clear_next_time = False

text_to_translate = st.text_area("✍️ 或手動輸入文字：", key="text_input_area", height=100)

if st.button("🚀 開始翻譯", type="primary"):
    if text_to_translate:
        try:
            is_ko = is_korean(text_to_translate)
            src_lang = 'ko' if is_ko else 'zh-TW'
            tgt_lang = 'zh-TW' if is_ko else 'ko'
            direction_label = "韓文 ➡️ 中文" if is_ko else "中文 ➡️ 韓文"

            # 根據引擎選擇不同的處理方式
            if engine_choice == "✨ 高級 AI (最準、較慢)":
                with st.spinner('AI 正在深度思考最道地的語氣...'):
                    # 呼叫 Pro 模型，最聰明但稍微等一下
                    translated = translate_with_ai(text_to_translate, GEMINI_API_KEY, 'gemini-2.5-pro')
                engine_used = "高級 AI"
            elif engine_choice == "⚡ 極速 AI (又快又準)":
                with st.spinner('AI 極速翻譯中...'):
                    # 呼叫剛剛測試成功的 Flash 模型，速度極快
                    translated = translate_with_ai(text_to_translate, GEMINI_API_KEY, 'gemini-2.5-flash')
                engine_used = "極速 AI"
            else:
                with st.spinner('使用一般 Google 翻譯...'):
                    translator = GoogleTranslator(source=src_lang, target=tgt_lang)
                    translated = translator.translate(text_to_translate)
                engine_used = "一般 Google 翻譯"
            
            new_record = {
                'direction': direction_label,
                'source_lang': src_lang,
                'target_lang': tgt_lang,
                'source_text': text_to_translate,
                'translated_text': translated,
                'engine': engine_used
            }
            
            st.session_state.history.append(new_record)
            st.session_state.current_view = new_record
            st.session_state.clear_next_time = True
            st.rerun()
            
        except Exception as e:
            st.error(f"發生錯誤：請檢查 API 金鑰是否有效 ({e})")
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
            # 【修復1】將音檔寫入虛擬記憶體，不再存成實體檔案
            tts_src = gTTS(text=view['source_text'], lang=view['source_lang'])
            fp_src = io.BytesIO()
            tts_src.write_to_fp(fp_src)
            fp_src.seek(0) # 將讀取點移回開頭
            st.audio(fp_src, format='audio/mp3')

    with col2:
        st.markdown("**翻譯結果**")
        st.markdown(f"""
            <div style='font-size: 26px; font-weight: bold; color: #1E90FF; line-height: 1.4; padding: 10px; border-left: 5px solid #1E90FF; background-color: #f0f8ff;'>
                {view['translated_text']}
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔊 發音", key="btn_tgt"):
            # 【修復1】將音檔寫入虛擬記憶體
            tts_tgt = gTTS(text=view['translated_text'], lang=view['target_lang'])
            fp_tgt = io.BytesIO()
            tts_tgt.write_to_fp(fp_tgt)
            fp_tgt.seek(0)
            st.audio(fp_tgt, format='audio/mp3')

