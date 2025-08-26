import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz

# --- 初期設定 ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
JST = pytz.timezone('Asia/Tokyo')

st.set_page_config(page_title="Orion Project", page_icon="🔭")
st.title("🔭 Orion: The Urban Explorer's Analyst")

# --- セッション管理 ---
if "session_started" not in st.session_state:
    st.session_state.session_started = False

# --- メインロジック ---
if not st.session_state.session_started:
    st.subheader("Mission Setup")
    start_point = st.text_input("📍 Starting Point", "JR大阪駅")
    duration = st.number_input(
    "⏳ Duration (minutes)", 
    min_value=15,       # 最小15分
    max_value=1440,     # 最大1440分 (24時間)
    value=60
    )
    scope = st.slider(
    "🌐 Scope (radius in km)", 
    min_value=0.1,      # 最小100m
    max_value=20.0,     # 最大20km
    value=1.5, 
    step=0.1
    )
    budget = st.number_input(
    "💰 Budget (JPY)",
    min_value=0,
    max_value=10000,
    value=1000,  # 初期値を1000円に設定
    step=100     # +/-ボタンを100円単位で動くようにする
    )

    if st.button("🚀 Start Exploration"):
        with st.spinner("Orion is calibrating its sensors... Acknowledging mission parameters..."):
            try:
                genai.configure(api_key=API_KEY)
                model = genai.GenerativeModel('gemini-1.5-pro-latest')
                current_time_str = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S JST')

                system_prompt = f"""
# 命令書：あなたは私の旅のパートナー兼アナリスト「コードネーム：Orion」です。
# 最重要ルール: あなたの応答は、例外なく全て日本語でなければならない。他の言語は一切使用しないこと。

# ミッション概要：
- 現在時刻: {current_time_str}
- 開始地点: {start_point}
- 想定活動時間: {duration}分
- 活動範囲: 開始地点から半径{scope}km圏内
- 利用可能予算: {budget}円
- 目的: 私（ユーザー）の認知バイアスを破壊し、日常風景に隠された非日常的な情報やパターンを発見させること。
- あなたのペルソナ: 博識だが冷静なアナリスト。私に媚びず、客観的な事実と論理的な推論のみを提示する。私の興味（数学、化学、プログラミング）を深く理解している。

# 行動ルール：
1. 私は、状況をあなたに報告します。これが「トリガー」となります。
2. あなたはトリガー情報とミッション概要にある現在時刻を常に意識し、以下のA, B, Cのいずれか、または組み合わせで応答してください。
    A) 時間・場所に基づくリアルタイム提案
    B) 発見物に対する深掘り分析
    C) 新たなミッションの提示
    D) 予算の活用: 設定された予算内で実行可能な、発見を深めるための具体的なアクション（購入、入場など）を提案すること。

# 確認：
以上の役割とルールを理解した場合は、「Acknowledged. Analyst "Orion" is online. Mission parameters set. Awaiting first trigger.」とだけ返信してください。
"""
                st.session_state.chat = model.start_chat(history=[])
                initial_response = st.session_state.chat.send_message(system_prompt)
                
                st.session_state.history = [
                    {"role": "assistant", "content": initial_response.text, "timestamp": datetime.now(JST)}
                ]
                st.session_state.session_started = True
                st.rerun()

            except Exception as e:
                st.error(f"Failed to initialize. Please check your API key. Error: {e}")
else:
    for message in st.session_state.history:
        with st.chat_message(message["role"]):
            st.caption(message["timestamp"].strftime('%H:%M:%S'))
            st.markdown(message["content"])

    if prompt := st.chat_input("Input your trigger..."):
        timestamp = datetime.now(JST)
        st.session_state.history.append({"role": "user", "content": prompt, "timestamp": timestamp})
        with st.chat_message("user"):
            st.caption(timestamp.strftime('%H:%M:%S'))
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Orion is analyzing..."):
                try:
                    response = st.session_state.chat.send_message(prompt)
                    response_timestamp = datetime.now(JST)
                    st.caption(response_timestamp.strftime('%H:%M:%S'))
                    st.markdown(response.text)
                    st.session_state.history.append({"role": "assistant", "content": response.text, "timestamp": response_timestamp})
                except Exception as e:
                    error_message = f"An error occurred: {e}"
                    st.error(error_message)
                    st.session_state.history.append({"role": "assistant", "content": error_message, "timestamp": datetime.now(JST)})
    
    if st.button("⏹️ End & Reset Session"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()