"""
Pure display helpers for the RAG Pipeline Streamlit UI.
"""

import streamlit as st
import datetime

def render_status_badge(status: str) -> str:
    color = "#6b7280"
    label = status.title()
    if status == "ready":
        color = "#16a34a"
        label = "Ready"
    elif status == "processing":
        color = "#d97706"
        label = "Processing"
    elif status == "failed":
        color = "#dc2626"
        label = "Failed"
        
    return f'<span style="background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:0.8rem;">{label}</span>'

def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def render_document_card(document: dict) -> None:
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(document.get("original_filename", "Unknown File"))
            file_type = document.get("file_type", "unknown")
            size = format_file_size(document.get("file_size_bytes", 0))
            st.write(f"Type: {file_type} | Size: {size}")
            
            pages = document.get("total_pages", 0)
            chunks = document.get("total_chunks", 0)
            st.write(f"Pages: {pages} | Chunks: {chunks}")
            
            uploaded_at = document.get("uploaded_at", "")
            if uploaded_at:
                # Basic string formatting if it's an ISO format string
                try:
                    dt = datetime.datetime.fromisoformat(uploaded_at.replace("Z", "+00:00"))
                    uploaded_at = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass
            st.write(f"Uploaded at: {uploaded_at}")
            
            status = document.get("status", "unknown")
            if status == "failed" and document.get("error_message"):
                st.markdown(f'<p style="color:#dc2626;">Error: {document["error_message"]}</p>', unsafe_allow_html=True)
                
        with col2:
            st.markdown(render_status_badge(document.get("status", "unknown")), unsafe_allow_html=True)

def render_chunk_card(chunk: dict, index: int) -> None:
    doc_id = chunk.get("document_id", "?")
    page = chunk.get("page_number", "?")
    title = f"Chunk {index} | Document ID: {doc_id} | Page: {page}"
    
    with st.expander(title):
        score = chunk.get("similarity_score")
        if score is not None:
            st.write(f"Score: {score:.3f}")
        st.text_area("Content", chunk.get("content", ""), height=120, disabled=True, key=f"chunk_{doc_id}_{index}")

def render_answer_box(answer: str) -> None:
    st.markdown("**Answer**")
    html = f"""
    <div style="background: #eff6ff; border-left: 4px solid #1a56db; padding: 16px; border-radius: 6px; font-size: 1rem; color: #1e293b;">
        {answer}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_metric_row(total_documents: int, total_chunks: int, status: str) -> None:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Documents", total_documents)
    with col2:
        st.metric("Indexed Chunks", total_chunks)
    with col3:
        st.metric("Backend Status", status)
