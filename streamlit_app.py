import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

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

# Get API key from user input
gemini_api_key = st.text_input("Gemini APIキーを入力してください", type="password")
if not gemini_api_key:
    st.error("Gemini APIキーを入力してください", icon="🚨")
    st.stop()

# Configure Gemini API
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-pro')

# Let the user upload a file via `st.file_uploader`.
uploaded_file = st.file_uploader(
    "Upload a document (.txt or .md)", type=("txt", "md")
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

if uploaded_file and (template_name != "カスタム質問" or question):
    # Process the uploaded file and question.
    document = uploaded_file.read().decode()
    
    # テンプレートに基づいてプロンプトを生成
    prompt = PROMPT_TEMPLATES[template_name].format(
        document=document,
        question=question
    )

    # Generate an answer using the Gemini API
    response = model.generate_content(prompt, stream=True)

    # Stream the response to the app
    for chunk in response:
        st.write(chunk.text)
