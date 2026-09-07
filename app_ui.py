import hashlib

import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/query"
UPLOAD_URL = "http://127.0.0.1:8000/upload"

# Set Streamlit page config
st.set_page_config(page_title="AI-Powered Knowledge Assistant", page_icon="🤖")

# Title
st.title("📚 AI-Powered Knowledge Assistant")

# Sidebar for file upload
st.sidebar.header("📂 Upload Documents")

# File uploader
uploaded_file = st.sidebar.file_uploader("Upload a document (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

# Upload and index a newly selected document
if uploaded_file:
    file_hash = hashlib.sha256(uploaded_file.getvalue()).hexdigest()
    if st.session_state.get("uploaded_file_hash") != file_hash:
        try:
            upload_response = requests.post(
                UPLOAD_URL,
                files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                timeout=120,
            )
            upload_response.raise_for_status()
            indexed_file = upload_response.json()
            st.session_state.uploaded_file_hash = file_hash
            st.session_state.document_filename = indexed_file["filename"]
            st.sidebar.success(f"{indexed_file['filename']} indexed ({indexed_file['chunks_indexed']} chunks)")
        except requests.RequestException as error:
            st.sidebar.error(f"Could not index the document: {error}")

if st.session_state.get("document_filename"):
    st.sidebar.caption(f"Querying: {st.session_state.document_filename}")

# Chat-like UI
st.subheader("💬 Ask a Question")
user_query = st.text_input("Type your question:")

# Send query to API
if st.button("Ask AI"):
    if user_query:
        document_filename = st.session_state.get("document_filename")
        if not document_filename:
            st.warning("Upload a document before asking a question.")
            st.stop()

        try:
            response = requests.post(
                API_URL,
                json={"query": user_query, "document_filename": document_filename},
                timeout=120,
            )
            response.raise_for_status()
            answer = response.json().get("response", "No response available.")
            st.markdown(f"**🤖 AI Response:** {answer}")
        except requests.RequestException as error:
            st.error(f"Could not get an answer: {error}")
    else:
        st.warning("Please enter a question.")





