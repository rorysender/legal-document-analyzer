
"""
Legal Document Analyzer

A Streamlit application that uses LlamaIndex and OpenAI to
analyze legal documents through Retrieval-Augmented Generation
(RAG).

Supports PDF, DOCX, and TXT documents.
"""

# Standard library imports
import os
import tempfile

# Third-party libraries
import streamlit as st
from docx import Document

# LlamaIndex document readers and indexing components
from llama_index.readers.file import PDFReader
from llama_index.core import (
    Document as LlamaDocument,
    VectorStoreIndex,
    SimpleDirectoryReader,
)


# ---------------------------------------------------------
# Streamlit Application Configuration
# ---------------------------------------------------------

# Configure the browser tab and application layout
st.set_page_config(
    page_title="Legal Document Analyzer",
    layout="wide"
)

st.title("Legal Document Analyzer")

# Allow users to upload supported legal document formats
uploaded_file = st.file_uploader(
    "Upload a contract",
    type=["txt", "pdf", "docx"],
    help="Upload a .txt, .pdf, or .docx agreement to analyze."
)


# ---------------------------------------------------------
# Document Processing and RAG Pipeline
# ---------------------------------------------------------

def build_query_engine_from_uploaded_file(uploaded_file):
    """
    Process an uploaded document and create a LlamaIndex query engine.

    The function saves the uploaded file temporarily, extracts
    its text using a format-specific reader, and constructs a
    vector index for semantic retrieval.

    Args:
        uploaded_file: A Streamlit UploadedFile object containing
            a PDF, DOCX, or TXT document.

    Returns:
        A LlamaIndex query engine capable of answering
        natural-language questions about the document.
    """

    # Automatically remove temporary files after processing
    with tempfile.TemporaryDirectory() as temp_dir:

        # Save the uploaded document for file-based readers
        file_path = os.path.join(temp_dir, uploaded_file.name)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Select a reader based on the document format
        if uploaded_file.name.lower().endswith(".pdf"):

            # Extract text from PDF pages
            documents = PDFReader().load_data(file=file_path)

        elif uploaded_file.name.lower().endswith(".docx"):

            # Open the Word document
            word_doc = Document(file_path)
            text_parts = []

            # Extract paragraph and table content in document order
            for block in word_doc.iter_inner_content():

                if hasattr(block, "text"):
                    text_parts.append(block.text)

                else:
                    # Preserve table rows as readable text
                    for row in block.rows:
                        text_parts.append(
                            " | ".join(
                                cell.text for cell in row.cells
                            )
                        )

            # Convert extracted text into a LlamaIndex document
            text = "\n".join(text_parts)
            documents = [LlamaDocument(text=text)]

        else:
            # Use LlamaIndex's default reader for TXT files
            documents = SimpleDirectoryReader(
                input_files=[file_path]
            ).load_data()

        # Generate embeddings and construct a vector index
        # for semantic retrieval of document content
        index = VectorStoreIndex.from_documents(documents)

        # Create a query engine that retrieves relevant passages
        # and uses an LLM to generate context-aware responses
        query_engine = index.as_query_engine()

    return query_engine


# ---------------------------------------------------------
# Document Upload and Index Initialization
# ---------------------------------------------------------

query_engine = None

if uploaded_file is not None:

    st.success(f"Loaded file: {uploaded_file.name}")

    # Process the uploaded document before accepting queries
    with st.spinner("Indexing uploaded document..."):
        query_engine = build_query_engine_from_uploaded_file(
            uploaded_file
        )

    # -----------------------------------------------------
    # Predefined Contract Analysis Queries
    # -----------------------------------------------------

    st.subheader("Quick Actions")

    # Arrange analysis options in a three-column layout
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)
    col7, col8, col9 = st.columns(3)

    preset_query = None

    # Each button maps to a predefined natural-language prompt
    if col1.button("Summarize"):
        preset_query = "Summarize this agreement."

    if col2.button("Risks"):
        preset_query = "List the main risks in this agreement."

    if col3.button("Obligations"):
        preset_query = "List the main obligations in this agreement."

    if col4.button("Penalties / Remedies"):
        preset_query = (
            "What penalties or remedies are described for breach?"
        )

    if col5.button("Non-Compete"):
        preset_query = (
            "What non-compete restrictions are imposed?"
        )

    if col6.button("Confidential Info"):
        preset_query = (
            "What confidential information is protected "
            "in this agreement?"
        )

    if col7.button("Hidden Value"):

        # Identify clauses with potential economic consequences,
        # including provisions without explicit monetary amounts
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

    # -----------------------------------------------------
    # Custom Natural-Language Queries
    # -----------------------------------------------------

    st.subheader("Ask a Custom Question")

    user_query = st.text_input(
        "Enter your question about the document:"
    )

    # Prioritize custom input when present; otherwise use
    # the selected predefined analysis prompt
    final_query = user_query if user_query else preset_query

    # -----------------------------------------------------
    # Query Execution and Response Display
    # -----------------------------------------------------

    if final_query:

        # Retrieve relevant document context and generate an answer
        with st.spinner("Analyzing document..."):
            response = query_engine.query(final_query)

        # Use a separate heading for economic value analysis
        if (
            "economic value" in final_query.lower()
            or "value or risk" in final_query.lower()
        ):
            st.subheader("Hidden Value Analysis")
        else:
            st.subheader("Response")

        # Display the generated response
        st.write(str(response))

        # -------------------------------------------------
        # Retrieved Source Excerpts
        # -------------------------------------------------

        # Display supporting passages returned by LlamaIndex
        # to help users inspect the context behind each answer
        if hasattr(response, "source_nodes") and response.source_nodes:

            st.subheader("Sources")

            for i, node in enumerate(response.source_nodes):

                st.markdown(f"**Source {i+1}:**")

                # Limit displayed excerpts to 300 characters
                # to keep the interface concise
                snippet = node.text.strip()

                snippet = (
                    snippet[:300] + "..."
                    if len(snippet) > 300
                    else snippet
                )

                st.write(snippet)
                st.divider()

else:
    # Display instructions until a document is uploaded
    st.info(
        "Upload a TXT, DOCX, or PDF document to analyze "
        "its terms, risks, and obligations."
    )

