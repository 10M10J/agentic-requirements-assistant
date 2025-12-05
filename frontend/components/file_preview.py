import streamlit as st
from PyPDF2 import PdfReader

def preview_file(uploaded_file):
    ext = uploaded_file.name.split(".")[-1].lower()

    st.subheader("📄 File Preview")

    if ext == "txt":
        text = uploaded_file.read().decode("utf-8")
        st.text_area("Text Preview", text, height=300)

    elif ext == "md":
        text = uploaded_file.read().decode("utf-8")
        st.markdown(text, unsafe_allow_html=True)

    elif ext == "pdf":
        try:
            reader = PdfReader(uploaded_file)
            pages = min(3, len(reader.pages))

            for i in range(pages):
                st.write(f"### Page {i+1}")
                st.write(reader.pages[i].extract_text())

        except Exception as e:
            st.error(f"Unable to preview PDF: {e}")

    else:
        st.warning(f"No preview available for file type: {ext}")
