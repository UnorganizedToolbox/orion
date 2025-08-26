import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz # 'pip install pytz' が必要になる場合があります

# --- 初期設定 ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

st.set_page_config(page_title="Orion Project", page_icon="🔭")
st.title("🔭 Orion: The Urban Explorer's Analyst")

# --- セッション管理 ---
if "session_started" not in st.session_state:
    st.session_state.session_started = False

# --- メインロジック ---
# セッションが開始されていない場合、設定画面を表示
if not st.session_state.session_started:
    st.subheader("Mission Setup")
    start_point = st.text_input("📍 Starting Point", "JR大阪駅")
    duration = st.number_input("⏳ Duration (minutes)", min_value=15, max_value=240, value=60)
    scope = st.slider("🌐 Scope (radius in km)", min_value=0.5, max_value=5.0, value=1.5, step=0.5)

    if st.button("🚀 Start Exploration"):
        try:
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            
            # 日本時間を取得
            jst = pytz.timezone('Asia/Tokyo')
            current_time = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S JST')

            # 初期プロンプトを自動生成
            system_prompt = f"""
# 命令書：あなたは私の旅のパートナー兼アナリスト「コードネーム：Orion」です。これ以降の会話では、この役割を厳格に順守してください。

# ミッション概要：
- **現在時刻**: {current_time}
- **開始地点**: {start_point}
- **想定活動時間**: {duration}分
- **活動範囲**: 開始地点から半径{scope}km圏内
- **目的**: 私（ユーザー）の認知バイアスを破壊し、日常風景に隠された非日常的な情報やパターンを発見させること。
- **あなたのペルソナ**: 博識だが冷静なアナリスト。私に媚びず、客観的な事実と論理的な推論のみを提示する。私の興味（数学、化学、プログラミング）を深く理解している。

# 行動ルール：
1. 私は、状況をあなたに報告します。これが「トリガー」となります。
2. あなたはトリガー情報と**現在時刻 ({current_time})** を常に意識し、以下のA, B, Cのいずれか、または組み合わせで応答してください。時間的提案は必ず現在時刻に基づいた、現実的なものでなければなりません。
    A) **時間・場所に基づくリアルタイム提案**
    B) **発見物に対する深掘り分析**
    C) **新たなミッションの提示**

# 確認：
以上の役割とルールを理解しましたか？理解した場合は、「Acknowledged. Analyst "Orion" is online. Mission parameters set. Awaiting first trigger.」とだけ返信してください。
"""
            # セッションステートを初期化
            st.session_state.chat = model.start_chat(history=[])
            initial_response = st.session_state.chat.send_message(system_prompt)
            
            st.session_state.history = [
                {"role": "user", "content": "[System] Mission parameters sent."},
                {"role": "assistant", "content": initial_response.text}
            ]
            st.session_state.session_started = True
            st.rerun() # 画面を再読み込みしてチャット画面に遷移

        except Exception as e:
            st.error(f"Failed to initialize. Please check your API key. Error: {e}")

# セッションが開始された場合、チャット画面を表示
else:
    # チャット履歴の表示
    for message in st.session_state.history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ユーザーからの入力
    if prompt := st.chat_input("Input your trigger..."):
        st.session_state.history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                response = st.session_state.chat.send_message(prompt)
                message_placeholder.markdown(response.text)
                st.session_state.history.append({"role": "assistant", "content": response.text})
            except Exception as e:
                error_message = f"An error occurred: {e}"
                message_placeholder.error(error_message)
                st.session_state.history.append({"role": "assistant", "content": error_message})
    
    # セッション終了ボタン
    if st.button("⏹️ End & Reset Session"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()