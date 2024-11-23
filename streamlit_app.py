import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import PyPDF2
import io
import openai
from anthropic import Anthropic
from google.ai import generativelanguage as glm
from google.api_core import client_options

# Load environment variables from .env file
load_dotenv()

# プロンプトテンプレートの定義
PROMPT_TEMPLATES = {
    "要約": "以下の文書を要約してください:\n{document}",
    "重要なポイント抽出": "以下の文書から重要なポイントを箇条書きで抽出してください:\n{document}",
    "財務分析": "以下の文書から財務に関する重要な情報を分析してください:\n{document}",
    "カスタム質問": "以下の文書について質問に答えてください:\n{document}\n\n質問: {question}"
}

# Show title and description.
st.title("📄 Financial Document Exstractor")
st.write(
    "Upload a document below and ask a question about it."
)

# モデル選択
model_option = st.selectbox(
    "使用するモデルを選択してください",
    ["Gemini-1.5-pro", "gpt-4o", "Claude-3-sonnet"],
    index=0
)

# APIキー入力
if model_option == "Gemini-1.5-pro":
    api_key = st.text_input("Gemini APIキーを入力してください", type="password")
    if not api_key:
        st.error("Gemini APIキーを入力してください", icon="🚨")
        st.stop()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
elif model_option == "gpt-4o":
    api_key = st.text_input("OpenAI APIキーを入力してください", type="password")
    if not api_key:
        st.error("OpenAI APIキーを入力してください", icon="🚨")
        st.stop()
    openai.api_key = api_key
elif model_option == "Claude-3-sonnet":
    api_key = st.text_input("Anthropic APIキーを入力してください", type="password")
    if not api_key:
        st.error("Anthropic APIキーを入力してください", icon="🚨")
        st.stop()
    anthropic = Anthropic(api_key=api_key)

# Let the user upload a file via `st.file_uploader`.
uploaded_file = st.file_uploader(
    "Upload a document (.txt, .md, or .pdf)", type=("txt", "md", "pdf")
)

# プロンプトテンプレートの選択
template_name = st.selectbox(
    "分析タイプを選択してください",
    options=list(PROMPT_TEMPLATES.keys()),
    disabled=not uploaded_file
)

# カスタム質問の入力欄（テンプレートが"カスタム質問"の場合のみ表示）
question = ""
if template_name == "カスタム質問":
    question = st.text_area(
        "文書について質問してください",
        placeholder="質問を入力してください",
        disabled=not uploaded_file,
    )

# 送信ボタンの追加（ファイルがアップロードされている場合のみ有効化）
submit_button = st.button("分析開始", disabled=not uploaded_file)

if submit_button and uploaded_file:
    # カスタム質問の場合は質問が入力されているかチェック
    if template_name == "カスタム質問" and not question:
        st.error("質問を入力してください")
    else:
        try:
            # Process the uploaded file based on its type
            if uploaded_file.type == "application/pdf":
                # PDFファイルの場合
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                document = ""
                for page in pdf_reader.pages:
                    document += page.extract_text() + "\n"
            else:
                # テキストファイルの場合
                document = uploaded_file.read().decode()
            
            # テンプレートに基づいてプロンプトを生成
            prompt = PROMPT_TEMPLATES[template_name].format(
                document=document,
                question=question
            )

            # Generate an answer based on selected model
            if model_option == "Gemini-1.5-pro":
                response = model.generate_content(prompt, stream=True)
                for chunk in response:
                    st.write(chunk.text)
            elif model_option == "gpt-4o":
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    stream=True
                )
                for chunk in response:
                    if "content" in chunk.choices[0].delta:
                        st.write(chunk.choices[0].delta.content)
            else:  # Claude-3-sonnet
                message = anthropic.messages.create(
                    model="claude-3-sonnet",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                st.write(message.content)
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")
