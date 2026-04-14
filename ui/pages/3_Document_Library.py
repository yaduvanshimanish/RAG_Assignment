import streamlit as st

st.set_page_config(
    page_title="Document Library - RAG Pipeline",
    layout="wide"
)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components import api_client, display_helpers

st.title("Document Library")
st.markdown("View, inspect, and delete your uploaded documents.")
st.markdown("---")

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    status_filter = st.selectbox("Filter by status", ["All", "ready", "processing", "failed"])
with col2:
    sort_order = st.selectbox("Sort by", ["Newest first", "Oldest first", "Most chunks", "Fewest chunks"])
with col3:
    refresh_button = st.button("Refresh")

status_filter_value = None if status_filter == "All" else status_filter.lower()

result = api_client.list_documents(limit=100, status_filter=status_filter_value)

if "error" in result:
    st.error(result["error"])
    st.stop()

documents = result.get("documents", [])

if sort_order == "Newest first":
    documents.sort(key=lambda d: d.get("uploaded_at", ""), reverse=True)
elif sort_order == "Oldest first":
    documents.sort(key=lambda d: d.get("uploaded_at", ""))
elif sort_order == "Most chunks":
    documents.sort(key=lambda d: d.get("total_chunks", 0), reverse=True)
elif sort_order == "Fewest chunks":
    documents.sort(key=lambda d: d.get("total_chunks", 0))

st.caption(f"Showing {len(documents)} document(s).")

if len(documents) == 0:
    st.info("No documents match the current filter.")
else:
    for document in documents:
        doc_col1, doc_col2 = st.columns([5, 1])
        
        with doc_col1:
            display_helpers.render_document_card(document)
            
        with doc_col2:
            view_chunks_button = st.button("View Chunks", key=f"chunks_{document.get('id')}")
            delete_button = st.button("Delete", key=f"delete_{document.get('id')}")
            
            if view_chunks_button:
                st.session_state["viewing_chunks_for"] = document.get("id")
                
            if delete_button:
                with st.spinner(f"Deleting document {document.get('id')}..."):
                    delete_result = api_client.delete_document(document.get("id"))
                if "error" in delete_result:
                    st.error(f"Delete failed: {delete_result['error']}")
                else:
                    st.success("Document deleted.")
                    st.rerun()

if "viewing_chunks_for" in st.session_state:
    doc_id = st.session_state["viewing_chunks_for"]
    st.markdown("---")
    st.subheader(f"Chunks for Document ID: {doc_id}")
    
    chunks = api_client.get_document_chunks(doc_id, limit=20)
    if not chunks:
        st.info("No chunks found for this document.")
    else:
        st.caption(f"Showing first {len(chunks)} chunks.")
        for i, chunk in enumerate(chunks, start=1):
            with st.expander(f"Chunk {chunk.get('chunk_index')} | Page {chunk.get('page_number', '?')}"):
                st.text_area(
                    "Content", chunk.get("content", ""),
                    height=120, disabled=True,
                    key=f"chunk_text_{doc_id}_{chunk.get('id')}"
                )
    
    if st.button("Close chunk viewer"):
        del st.session_state["viewing_chunks_for"]
        st.rerun()
