import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os

st.set_page_config(page_title="AI 雙向翻譯小幫手", page_icon="🇰🇷", layout="wide")

# ==========================================
# 1. 初始化與側邊欄設定
# ==========================================
if "history" not in st.session_state:
    st.session_state.history = []
if "current_view" not in st.session_state:
    st.session_state.current_view = None

with st.sidebar:
    st.header("⚙️ AI 引擎設定")
    # 這裡填入你剛才申請的免費 Gemini API Key
    gemini_key = st.text_input("輸入 Gemini API Key", type="password")
    
    st.divider()
    st.header("🕒 歷史翻譯紀錄")
    
    if st.button("🗑️ 清除所有紀錄"):
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

# ==========================================
# 2. 核心 AI 翻譯邏輯 (加入情境設定)
# ==========================================
def translate_with_ai(text, direction, api_key):
    genai.configure(api_key=api_key)
    # 使用免費且快速的 Flash 模型
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # 這裡就是 AI 翻譯最強大的地方：我們可以設定情境！
    if direction == "韓文 ➡️ 中文":
        prompt = f"""
        你是一個專業的韓文翻譯人員。請將以下韓文翻譯成流暢、自然的台灣繁體中文。
        這段文字可能來自韓國實況主的直播內容，請保留原文的口語化語氣、情緒，並精準翻譯韓國的網路用語。
        請直接輸出翻譯結果，不要加上任何解釋：
        {text}
        """
    else:
        prompt = f"""
        你是一個精通韓文的台灣人。請將以下中文翻譯成自然、道地的韓文。
        這是準備要在韓國實況主粉絲見面會上說的話，請使用適當的敬語（해요體或하십시오體），並帶有禮貌且溫暖的語氣。
        請直接輸出翻譯結果，不要加上任何解釋：
        {text}
        """
        
    response = model.generate_content(prompt)
    return response.text.strip()

# ==========================================
# 3. 主畫面區
# ==========================================
st.title("🇰🇷 AI 情境雙向翻譯與語音工具")

direction = st.radio("請選擇翻譯方向：", ["韓文 ➡️ 中文", "中文 ➡️ 韓文"], horizontal=True)

if direction == "韓文 ➡️ 中文":
    input_label = "請輸入韓文 (例如直播台詞)："
    src_lang = 'ko'
    tgt_lang = 'zh-TW'
else:
    input_label = "請輸入中文 (例如想對實況主說的話)："
    src_lang = 'zh-TW'
    tgt_lang = 'ko'

text_to_translate = st.text_area(input_label, placeholder="請在此輸入文字...", height=150)

if st.button("🚀 開始 AI 翻譯", type="primary"):
    if not gemini_key:
        st.error("請先在左側輸入 Gemini API Key 喔！")
    elif text_to_translate:
        try:
            with st.spinner('AI 正在思考最道地的翻譯...'):
                translated = translate_with_ai(text_to_translate, direction, gemini_key)
            
            new_record = {
                'direction': direction,
                'source_lang': src_lang,
                'target_lang': tgt_lang,
                'source_text': text_to_translate,
                'translated_text': translated,
                'engine': "Gemini AI"
            }
            
            st.session_state.history.append(new_record)
            st.session_state.current_view = new_record
            st.rerun()
            
        except Exception as e:
            st.error(f"翻譯發生錯誤，請檢查 API Key 或是網路連線。({e})")
    else:
        st.warning("請先輸入文字內容。")

st.divider()

# ==========================================
# 4. 顯示結果與語音播放區
# ==========================================
if st.session_state.current_view:
    view = st.session_state.current_view
    
    st.subheader("📝 翻譯結果")
    st.caption(f"模式：{view['direction']} | 使用引擎：{view['engine']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**原文**")
        st.write(view['source_text'])
        if st.button("🔊 聽原文發音", key="btn_src_main"):
            tts_src = gTTS(text=view['source_text'], lang=view['source_lang'])
            tts_src.save("src.mp3")
            st.audio("src.mp3", format='audio/mp3')

    with col2:
        st.markdown("**翻譯**")
        st.info(view['translated_text'])
        if st.button("🔊 聽翻譯發音", key="btn_tgt_main"):
            tts_tgt = gTTS(text=view['translated_text'], lang=view['target_lang'])
            tts_tgt.save("tgt.mp3")
            st.audio("tgt.mp3", format='audio/mp3')