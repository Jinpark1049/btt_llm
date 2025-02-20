import streamlit as st
import fitz  # PyMuPDF
import os
import re
from io import BytesIO
from streamlit_pdf_viewer import pdf_viewer
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from btt_parser import *

def main():
 
    st.set_page_config(
        page_title="BTT Report Extractor",
        page_icon="📁",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    col1, col2 = st.columns((1, 1), gap='medium')

    with st.sidebar:
        st.title('📁 BTT Report Extractor')
        
        # Year selection dropdown
        years = list(range(2000, 2031))
        selected_year = st.selectbox('Select a Year', years, index=years.index(2025))
        
        # File uploader
        st.sidebar.header("Upload PDF")
        uploaded_file = st.sidebar.file_uploader("Choose a PDF file", type=["pdf"])
        
        pdf_text = ""  # Initialize empty string to avoid errors

        if uploaded_file is not None:
            st.sidebar.success("File uploaded successfully!")

            # Save directory based on selected year
            save_dir = os.path.join("temp", str(selected_year))
            os.makedirs(save_dir, exist_ok=True)

            # Ensure filename is safe
            safe_file_name = re.sub(r'[<>:"/\\|?*]', '_', uploaded_file.name)
            save_path = os.path.join(save_dir, safe_file_name)

            # Save the file
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Extract text from PDF
            with fitz.open(save_path) as doc:
                pdf_text = "\n".join([page.get_text("text") for page in doc])

            # Store pdf_path and text in session_state for persistence
            st.session_state["pdf_path"] = save_path
            st.session_state["pdf_text"] = pdf_text
            st.session_state['binary_data'] = uploaded_file.getvalue()

    # Display extracted text in column 1
    with col1:
        if st.session_state.get("pdf_text"):
            st.markdown('<h4 style="text-align: center;">Extracted Text</h4>', unsafe_allow_html=True)
            st.text_area("Extracted PDF Content", st.session_state["pdf_text"], height=800)
        
    with col2:
        if st.session_state.get("binary_data"):
            st.markdown('<h4 style="text-align: center;">PDF Viewer</h4>', unsafe_allow_html=True)
            pdf_viewer(input=st.session_state['binary_data'], height=800)

if __name__ == "__main__":
    main()
