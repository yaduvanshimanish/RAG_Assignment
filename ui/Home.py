import streamlit as st

st.set_page_config(
    page_title="RAG Pipeline",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from components import api_client, display_helpers

# High-tech styling
st.markdown("""
<style>
.terminal-card {
    background-color: #0f172a;
    color: #38bdf8;
    border: 1px solid #1a56db;
    border-radius: 8px;
    padding: 20px;
    font-family: 'Courier New', Courier, monospace;
    box-shadow: 0 0 15px rgba(26, 86, 219, 0.4);
}
.glow-text {
    color: #1a56db;
    text-shadow: 0 0 8px rgba(26, 86, 219, 0.6);
}
.hr-tech {
    border: 0;
    height: 1px;
    background-image: linear-gradient(to right, rgba(26, 86, 219, 0), rgba(26, 86, 219, 0.75), rgba(26, 86, 219, 0));
}
</style>
""", unsafe_allow_html=True)

st.sidebar.title("RAG Pipeline")
st.sidebar.markdown("<hr class='hr-tech'>", unsafe_allow_html=True)
st.sidebar.markdown("Navigation is handled by the pages/ folder.")
st.sidebar.markdown("<hr class='hr-tech'>", unsafe_allow_html=True)

st.sidebar.subheader("System Configuration")
st.sidebar.code(f"API_BASE_URL:\n{api_client.API_BASE_URL}", language="text")

if st.sidebar.button("Refresh System Status"):
    st.session_state.clear()
    st.rerun()

st.markdown("<h1 class='glow-text'>RAG Pipeline // Core Interactive Node</h1>", unsafe_allow_html=True)
st.markdown("Advanced Retrieval-Augmented Generation architecture powered by Gemini Flash and FAISS vector index.")
st.markdown("<hr class='hr-tech'>", unsafe_allow_html=True)

st.subheader("System Diagnostics")

try:
    health_res = api_client.get_health()
except Exception as e:
    health_res = {"error": str(e)}

if "error" in health_res:
    st.error(f"Backend unavailable: {health_res['error']}")
    st.info("Steps to fix: check that the API is running and API_BASE_URL is correct.")
else:
    # Use terminal style display for health
    docs_count = health_res.get("documents_count", 0)
    chunks_count = health_res.get("chunks_count", 0) # Assuming the health endpoint might return these, if not we will just use placeholders or make a separate call.
    # Actually, the health response returns status. We can also call list_documents.
    
    docs_res = api_client.list_documents(limit=1)
    if "error" not in docs_res:
        total_documents = docs_res.get("total", 0)
    else:
        total_documents = 0
        
    term_html = f"""
    <div class="terminal-card">
        <div>[SYS] Connection Established to Backend Node.</div>
        <div>[SYS] Status: ONLINE</div>
        <div>[SYS] API Address: {api_client.API_BASE_URL}</div>
        <div>[DB] Indexed Documents: {total_documents}</div>
        <div>[DB] FAISS Vector Store: READY</div>
        <div style="margin-top:10px; color:#10b981;">>>> All systems operating within standard parameters.</div>
    </div>
    """
    st.markdown(term_html, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    display_helpers.render_metric_row(total_documents, -1, "Online") # -1 as placeholder for chunks since we don't have total chunks globally tracked easily without full fetch

st.markdown("<hr class='hr-tech'>", unsafe_allow_html=True)
st.subheader("Operation Protocols")
st.markdown("""
1. **Upload Documents**: Proceed to module `[1_Upload_Documents]` to ingest PDF, DOCX, or TXT artifacts for vectorization.
2. **Ask Questions**: Access module `[2_Ask_Questions]` to interrogate the knowledge base utilizing Gemini Flash AI parameters.
3. **Document Library**: Utilize module `[3_Document_Library]` to review or purge indexed artifacts and inspect chunk generation.
4. **Query History**: Load module `[4_Query_History]` to audit previous transmissions and AI inferences.
""")

st.markdown("<hr class='hr-tech'>", unsafe_allow_html=True)
st.caption("Powered by Google Gemini Flash and FAISS vector search.")
