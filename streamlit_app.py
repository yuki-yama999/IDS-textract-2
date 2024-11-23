import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Show title and description.
st.title("📄 Financial Document Exstractor")
st.write(
    "Upload a document below and ask a question about it."
)

# Get API key from environment variable
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    st.error("Gemini API key not found in environment variables.", icon="🚨")
    st.stop()

# Configure Gemini API
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-pro')

# Let the user upload a file via `st.file_uploader`.
uploaded_file = st.file_uploader(
    "Upload a document (.txt or .md)", type=("txt", "md")
)

# Ask the user for a question via `st.text_area`.
question = st.text_area(
    "Now ask a question about the document!",
    placeholder="Can you give me a short summary?",
    disabled=not uploaded_file,
)

if uploaded_file and question:

    # Process the uploaded file and question.
    document = uploaded_file.read().decode()
    prompt = f"Here's a document: {document} \n\n---\n\n {question}"

    # Generate an answer using the Gemini API
    response = model.generate_content(prompt, stream=True)

    # Stream the response to the app
    for chunk in response:
        st.write(chunk.text)
