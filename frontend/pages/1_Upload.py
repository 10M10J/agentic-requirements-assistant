import sys, os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

import streamlit as st
#from api_client import process_transcript
from backend.agents.pipeline import RequirementsPipeline

st.title("Upload Transcript")

uploaded_file = st.file_uploader(
    "Upload transcript file",
    type=["txt", "pdf", "docx", "md"]
)

# Only proceed if file is uploaded
if uploaded_file is not None:

    import docx2txt
    import PyPDF2

    content = ""

    # Extract text based on file type
    filename = uploaded_file.name.lower()

    if filename.endswith(".txt"):
        content = uploaded_file.read().decode("utf-8")

    elif filename.endswith(".pdf"):
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        content = "\n".join(
            page.extract_text() or ""
            for page in pdf_reader.pages
        )

    elif filename.endswith(".docx"):
        content = docx2txt.process(uploaded_file)

    elif filename.endswith(".md"):
        content = uploaded_file.read().decode("utf-8")

    # Validate extraction
    if not content.strip():
        st.error("Could not extract text from the uploaded file.")
        st.stop()

    # Show transcript preview
    st.write("### Transcript Preview")
    st.text_area("Raw Transcript", content, height=300)

    # Button to process
    if st.button("Process Transcript"):
        with st.spinner("Processing with AI..."):
            #result = process_transcript(content)
            pipeline = RequirementsPipeline()
            result = pipeline.run(content)

        st.session_state["pipeline_result"] = result

        st.success("Processing complete! Go to 'Generated Requirements' page.")
