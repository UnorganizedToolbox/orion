import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

# --- 初期設定 ---
# .envファイルからAPIキーを読み込む
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Streamlitのページ設定
st.set_page_config(page_title="Orion Project", page_icon="🔭")
st.title("🔭 Orion: The Urban Explorer's Analyst")

# --- Geminiモデルの初期化 ---
# セッションステートにモデルとチャット履歴がなければ初期化
if "gemini_model" not in st.session_state:
    try:
        genai.configure(api_key=API_KEY)
        st.session_state.gemini_model = genai.GenerativeModel('gemini-1.5-pro-latest')
        st.session_state.chat = st.session_state.gemini_model.start_chat(history=[])
        st.session_state.history = []
        st.info("Orion is online. Please provide your first trigger.")
    except Exception as e:
        st.error(f"Failed to initialize the model. Please check your API key. Error: {e}")
        st.stop()

# --- チャット履歴の表示 ---
for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- ユーザーからの入力 ---
if prompt := st.chat_input("Input your trigger (location, observation, etc.)"):
    # ユーザーの入力を履歴に追加して表示
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Geminiに応答を生成させて表示
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            # Gemini APIにプロンプトを送信
            response = st.session_state.chat.send_message(prompt, stream=True)
            for chunk in response:
                full_response += chunk.text
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"An error occurred: {e}")
            full_response = f"Error: {e}"

    # AIの応答を履歴に追加
    st.session_state.history.append({"role": "assistant", "content": full_response})