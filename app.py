import os
import tempfile
import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

st.set_page_config(page_title="Legal Document Analyzer", layout="wide")
st.title("Legal Document Analyzer")

uploaded_file = st.file_uploader(
    "Upload a contract",
    type=["txt", "pdf"],
    help="Upload a .txt or .pdf agreement to analyze."
)

def build_query_engine_from_uploaded_file(uploaded_file):
    # Create a temporary directory that is automatically cleaned up
    with tempfile.TemporaryDirectory() as temp_dir:

        # Save the uploaded document so LlamaIndex can read it
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Load the document into LlamaIndex
        documents = SimpleDirectoryReader(temp_dir).load_data()

        # Build a vector index for semantic document retrieval
        index = VectorStoreIndex.from_documents(documents)

        # Create the query engine before the temporary files are removed
        query_engine = index.as_query_engine()

    return query_engine

query_engine = None

if uploaded_file is not None:
    st.success(f"Loaded file: {uploaded_file.name}")
    with st.spinner("Indexing uploaded document..."):
        query_engine = build_query_engine_from_uploaded_file(uploaded_file)

    st.subheader("Quick Actions")

    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)
    col7, col8, col9 = st.columns(3)

    preset_query = None

    if col1.button("Summarize"):
        preset_query = "Summarize this agreement."
    if col2.button("Risks"):
        preset_query = "List the main risks in this agreement."
    if col3.button("Obligations"):
        preset_query = "List the main obligations in this agreement."
    if col4.button("Penalties / Remedies"):
        preset_query = "What penalties or remedies are described for breach?"
    if col5.button("Non-Compete"):
        preset_query = "What non-compete restrictions are imposed?"
    if col6.button("Confidential Info"):
        preset_query = "What confidential information is protected in this agreement?"
    if col7.button("Hidden Value"):
        preset_query = """
        Analyze this agreement and identify clauses that create economic value or risk even when no dollar amount is stated.

        For each clause you identify, provide:
        1. Clause type
        2. Who it affects
        3. Estimated economic impact (Low / Medium / High)
        4. Brief explanation of why
        5. The relevant contract language

        Focus on things like non-compete, confidentiality, exclusivity, IP ownership, termination rights, indemnification, and restrictions on future business activity.
        """
    st.subheader("Ask a Custom Question")
    user_query = st.text_input("Enter your question about the document:")

    final_query = user_query if user_query else preset_query

    if final_query:
        with st.spinner("Analyzing document..."):
            response = query_engine.query(final_query)

        if "economic value" in final_query.lower() or "value or risk" in final_query.lower():
            st.subheader("Hidden Value Analysis")
        else:
            st.subheader("Response")

        st.write(str(response))

        if hasattr(response, "source_nodes") and response.source_nodes:
            st.subheader("Sources")
            for i, node in enumerate(response.source_nodes):
                st.markdown(f"**Source {i+1}:**")
                snippet = node.text.strip()
                snippet = snippet[:300] + "..." if len(snippet) > 300 else snippet
                st.write(snippet)
                st.divider()
else:
    st.info("Upload a .txt or .pdf contract to begin.")

