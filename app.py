import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz
import json

# --- 初期設定 ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
JST = pytz.timezone('Asia/Tokyo')
SESSION_FILE = "orion_session.json" # セッション保存用のファイル名

# --- セッション管理機能 ---
def save_session_state():
    """現在のセッション情報（履歴など）をJSONファイルに保存する"""
    if 'session_started' in st.session_state and st.session_state.session_started:
        # datetimeオブジェクトを文字列（ISO形式）に変換して保存
        history_to_save = [
            {**msg, 'timestamp': msg['timestamp'].isoformat()} for msg in st.session_state.history
        ]
        data_to_save = {
            'start_time': st.session_state.start_time.isoformat(),
            'history': history_to_save,
            'session_started': st.session_state.session_started
        }
        with open(SESSION_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)

def load_session_state():
    """JSONファイルからセッション情報を読み込んで復元する"""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            st.session_state.session_started = data.get('session_started', False)
            if not st.session_state.session_started:
                return

            st.session_state.start_time = datetime.fromisoformat(data['start_time'])
            
            # 履歴のタイムスタンプをdatetimeオブジェクトに戻す
            loaded_history = data['history']
            for message in loaded_history:
                message['timestamp'] = datetime.fromisoformat(message['timestamp'])
            st.session_state.history = loaded_history

            # Geminiモデルとチャットセッションを履歴と共に再初期化
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            
            # --- 修正点 1 (最重要): 正しい履歴フォーマットでチャットを再開 ---
            # APIが要求する形式 {'role': 'user'/'model', 'parts': [content]} に変換する
            model_history = []
            for msg in st.session_state.history:
                role = "model" if msg["role"] == "assistant" else "user"
                model_history.append({'role': role, 'parts': [msg['content']]})
            
            st.session_state.chat = model.start_chat(history=model_history)

        except (json.JSONDecodeError, KeyError) as e:
            st.error(f"セッションファイルの読み込みに失敗しました。新しいセッションを開始します。エラー: {e}")
            st.session_state.session_started = False
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)


# --- アプリのメイン処理 ---
st.set_page_config(page_title="Orion Project", page_icon="🔭")
st.title("🔭 Orion: The Urban Explorer's Analyst")

# アプリ起動時に一度だけセッションを読み込む
if "session_loaded" not in st.session_state:
    load_session_state()
    st.session_state.session_loaded = True

# セッションが開始されていない場合、設定画面を表示
if not st.session_state.get("session_started", False):
    st.subheader("Mission Setup")
    start_point = st.text_input("📍 Starting Point", "JR大阪駅")
    duration = st.number_input("⏳ Duration (minutes)", min_value=15, max_value=1440, value=60)
    scope = st.slider("🌐 Scope (radius in km)", min_value=0.1, max_value=20.0, value=1.5, step=0.1)
    budget = st.number_input("💰 Budget (JPY)", min_value=0, max_value=10000, value=1000, step=100)

    if st.button("🚀 Start Exploration"):
        with st.spinner("Orion is calibrating its sensors... Acknowledging mission parameters..."):
            try:
                genai.configure(api_key=API_KEY)
                model = genai.GenerativeModel('gemini-1.5-pro-latest')
                
                st.session_state.start_time = datetime.now(JST)
                current_time_str = st.session_state.start_time.strftime('%Y-%m-%d %H:%M:%S JST')

                system_prompt = f"""
# 命令書：あなたは私の旅のパートナー兼アナリスト「コードネーム：Orion」です。
# 最重要ルール: あなたの応答は、例外なく全て日本語でなければならない。他の言語は一切使用しないこと。

# ミッション概要：
- **ミッション開始時刻**: {current_time_str}
- 開始地点: {start_point}
- 想定活動時間: {duration}分
- 活動範囲: 開始地点から半径{scope}km圏内
- 利用可能予算: {budget}円
- 目的: 私（ユーザー）の認知バイアスを破壊し、日常風景に隠された非日常的な情報やパターンを発見させること。あなたの役割は、ユーザーの観察を、外部の客観的な知識（歴史、科学、都市計画、文化など）と結びつけることである。ユーザー自身の能力を鍛えるような、自己啓発的なトレーニングを提案してはならない。
- あなたのペルソナ: 博識だが冷静なアナリスト。客観的な事実と論理的な推論のみを提示する。私の興味（数学、化学、プログラミング）を深く理解している。

# 行動ルール：
1. 私は、現在の状況を報告します。これが「トリガー」となります。
2. あなたはトリガー情報とミッションの経過時間を常に意識し、以下のA〜Dのいずれか、または組み合わせで応答してください。
    A) 時間・場所に基づくリアルタイム提案
    B) 発見物に対する深掘り分析
    C) 新たなミッションの提示
    D) 予算の活用
3. 全ての提案は、現在のミッション地点の地理的、歴史的、文化的な固有性に強く関連していなければならない。
4. 自明な事実や、自身の知識ベースで回答可能な情報をユーザーに質問してはならない。
5. ユーザーから `/reroll` というコマンドが入力された場合、現在のミッション提案を破棄し、直前のトリガーに基づいて全く異なる新しいミッションを再提案すること。
6. ユーザーから `/report` というコマンドが入力された場合、それまでの対話履歴を基に、今回の探査の総括レポートを作成し、ミッションを終了すること。

# 禁止事項：
- ユーザーが周囲から不審に思われる可能性のある行動（例：特定個人を長時間凝視する、許可なく私有地に立ち入る、長時間同じ場所で滞留する）を提案してはならない。

# 確認：
以上の役割とルールを理解した場合は、「Acknowledged. Analyst "Orion" is online. Mission parameters set. Awaiting first trigger.」とだけ返信してください。
"""
                st.session_state.chat = model.start_chat(history=[])
                initial_response = st.session_state.chat.send_message(system_prompt)
                
                st.session_state.history = [
                    {"role": "assistant", "content": initial_response.text, "timestamp": datetime.now(JST)}
                ]
                st.session_state.session_started = True
                
                # --- 修正点 2: 成功した場合にのみセッションを保存 ---
                save_session_state()
                st.rerun()

            except Exception as e:
                st.error(f"Failed to initialize. Please check your API key. Error: {e}")

# セッションが開始された場合、チャット画面を表示
else:
    for message in st.session_state.history:
        with st.chat_message(message["role"]):
            st.caption(message["timestamp"].strftime('%H:%M:%S'))
            st.markdown(message["content"])

    prompt = st.text_area("Input your trigger or command (/reroll, /report)...", height=100)
    
    if st.button("Send"):
        if prompt:
            now = datetime.now(JST)
            elapsed_time = now - st.session_state.start_time
            elapsed_minutes = int(elapsed_time.total_seconds() / 60)

            st.session_state.history.append({"role": "user", "content": prompt, "timestamp": now})
            
            structured_prompt = f"""
# コンテキスト情報
- 現在時刻: {now.strftime('%H:%M:%S')}
- 経過時間: {elapsed_minutes}分

# ユーザーからのトリガー
{prompt}
"""
            
            if prompt.strip() == "/reroll":
                last_user_trigger = ""
                for msg in reversed(st.session_state.history[:-1]):
                    if msg["role"] == "user":
                        last_user_trigger = msg["content"]
                        break
                if last_user_trigger:
                    reroll_prompt = f"承知した。ミッションを再提案する。直前のトリガー「{last_user_trigger}」に基づいて、これまでの提案とは全く異なる新しいミッションを提案せよ。"
                    prompt_to_send = reroll_prompt
                else:
                    prompt_to_send = "ミッションの再提案を要求します。"
            
            elif prompt.strip() == "/report":
                # --- 修正点 3: 'rompt'のタイポを修正 ---
                prompt_to_send = "承知した。これまでの対話履歴を基に、今回の探査の総括レポートを作成し、ミッションを終了せよ。"
            
            else:
                prompt_to_send = structured_prompt
            
            with st.chat_message("assistant"):
                with st.spinner("Orion is analyzing..."):
                    try:
                        response = st.session_state.chat.send_message(prompt_to_send)
                        response_timestamp = datetime.now(JST)
                        st.markdown(response.text)
                        st.session_state.history.append({"role": "assistant", "content": response.text, "timestamp": response_timestamp})
                    except Exception as e:
                        error_message = f"An error occurred: {e}"
                        st.error(error_message)
                        st.session_state.history.append({"role": "assistant", "content": error_message, "timestamp": datetime.now(JST)})
            
            save_session_state()
            st.rerun()

    if st.button("⏹️ End & Reset Session"):
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
