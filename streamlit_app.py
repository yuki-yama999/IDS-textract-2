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
    "国内債券 公募上場・非上場普通債券属性": """入力された国内債券に関するドキュメントを読み取り、以下の項目に対する情報を抽出して表形式で教えてください。
なお、表形式は、項目、内容、根拠の形式で出力してください。
根拠には、引用箇所の該当ページ数と元の文章を記載してください。

#抽出したい項目
・償還日（YYYYMMDD形式で）
・銘柄名称
・募集方式区分（公募債なら１　非公募債なら２）
・利払日１（MMDD形式　複数ある場合は次の項目に記載）
・利払日２（MMDD形式）
・利払日３（MMDD形式）
・利払日４（MMDD形式）
・商品種別（下記のいずれかに分類して）
A0 ： 割引短期国債等
A1 ： 利付国債
A2 ： 割引国債
B0 ： 地方債
C0 ： 政府保証債・非政府保証債
E0 ： 特殊債(東京交通債券・放送債券)
F0 ： 利付電々債
G0 ： 割引電々債
H0 ： 利付金融債
I1 ： 割引みずほ銀行債券
I2 ： 割引商工債券
I3 ： 割引農林債券
I4 ： 割引長期信用債券
I5 ： 割引あおぞら債券
I6 ： 割引東京三菱銀行債券
J1～9 ： 事業債
K1～9 ： 電力債
ZS ： 円建外債（国債）
ZT ： 円建外債（地方債）
ZX ： 円建外債（その他債）
・利割区分（1 ： 利付債 2 ： 割引債）
・利払方式区分（0 ： 割引債 　1 ： 固定利付債　 2 ： 変動利付債 　3 ： ステップ債）
\n{document}""",
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
