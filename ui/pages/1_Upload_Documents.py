import streamlit as st

st.set_page_config(
    page_title="Upload Documents - RAG Pipeline",
    layout="wide"
)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components import api_client, display_helpers

st.title("Upload Documents")
st.markdown("Upload PDF, DOCX, or TXT files. Maximum 100MB per file. Maximum 20 documents.")
st.markdown("---")

with st.form("upload_form"):
    uploaded_file = st.file_uploader(
        "Choose a document",
        type=["pdf", "docx", "doc", "txt", "md"],
        help="Supported formats: PDF, DOCX, DOC, TXT, MD"
    )
    submit_button = st.form_submit_button("Upload and Process")

if submit_button:
    if uploaded_file is not None:
        st.info("Uploading and processing your document. This may take a minute...")
        response = api_client.upload_document(
            uploaded_file.read(),
            uploaded_file.name,
            uploaded_file.type
        )
        if "error" in response:
            st.error(f"Upload failed: {response['error']}")
        else:
            # Handle the response structure properly. It might be a list or a single object based on backend update.
            # Assuming recent change makes it return list of uploaded docs
            doc_data = response[0] if isinstance(response, list) and len(response) > 0 else response
            st.success(f"Document uploaded successfully. Status: {doc_data.get('status', 'unknown')}")
            
            if doc_data.get("status") == "failed":
                st.error(f"Processing failed: {doc_data.get('error_message', 'Unknown error')}")
            else:
                st.info(f"Pages: {doc_data.get('total_pages', 0)} | Chunks: {doc_data.get('total_chunks', 0)}")
    else:
        st.warning("Please select a file before uploading.")

st.markdown("---")
st.subheader("Current Documents")

result = api_client.list_documents(limit=100)
if "error" in result:
    st.error(result["error"])
elif result.get("total", 0) == 0:
    st.info("No documents uploaded yet.")
else:
    st.caption(f"{result.get('total', 0)} document(s) in the system.")
    for document in result.get("documents", []):
        display_helpers.render_document_card(document)
