import streamlit as st
import time

st.set_page_config(
    page_title="Ask Questions - RAG Pipeline",
    layout="wide"
)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components import api_client, display_helpers

st.title("Ask Questions")
st.markdown("Ask a question and the AI will answer using your uploaded documents.")
st.markdown("---")

all_docs_result = api_client.list_documents(limit=100, status_filter="ready")
ready_documents = all_docs_result.get("documents", [])

if len(ready_documents) == 0:
    st.warning("No documents are ready. Please upload documents first.")
    st.stop()

st.sidebar.subheader("Query Settings")

top_k = st.sidebar.slider(
    "Number of chunks to retrieve",
    min_value=1, max_value=20, value=5,
    help="More chunks give richer context but may slow generation."
)

use_filter = st.sidebar.checkbox("Filter by specific documents", value=False)
selected_document_ids = None

if use_filter:
    doc_options = {f"{d.get('original_filename')} (ID: {d.get('id')})": d.get('id') for d in ready_documents}
    selected_labels = st.sidebar.multiselect(
        "Select documents to search",
        options=list(doc_options.keys()),
        default=[]
    )
    selected_document_ids = [doc_options[label] for label in selected_labels]

query_text = st.text_area(
    "Your question",
    placeholder="Example: What are the main conclusions of the report?",
    height=100,
    max_chars=2000
)

ask_button = st.button("Ask", type="primary", use_container_width=False)

if ask_button:
    if not query_text.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Searching documents and generating answer..."):
            start = time.time()
            result = api_client.query_documents(
                query_text.strip(), top_k, selected_document_ids
            )
            elapsed = time.time() - start

        if "error" in result:
            st.error(f"Query failed: {result['error']}")
        else:
            st.markdown("---")
            
            answer = result.get("answer", "No answer generated.")
            display_helpers.render_answer_box(answer)
            
            p_time_ms = result.get("processing_time_ms", elapsed * 1000)
            sources = result.get("sources", [])
            sources_str = ", ".join(sources) if sources else "N/A"
            
            st.caption(f"Answer generated in {p_time_ms:.0f} ms | Sources: {sources_str}")
            
            st.markdown("---")
            retrieved_chunks = result.get("retrieved_chunks", [])
            st.subheader(f"Retrieved Chunks ({len(retrieved_chunks)})")
            
            for i, chunk in enumerate(retrieved_chunks, start=1):
                display_helpers.render_chunk_card(chunk, i)
