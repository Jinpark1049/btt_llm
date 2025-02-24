import streamlit as st
import fitz  # PyMuPDF
import os
import re
from io import BytesIO
from streamlit_pdf_viewer import pdf_viewer
import sys
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

st.set_page_config(
    page_title="BTT Report Extractor",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "run_chat_assistant" not in st.session_state:
    st.session_state.run_chat_assistant = False

if "run_llm_parser" not in st.session_state:
    st.session_state.run_llm_parser = False

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from btt_parser import *

@st.cache_resource
def load_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True},
    )

def main(embeddings_model):
    
    st.session_state["embeddings_model"] = embeddings_model
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
            # 만약 이전에 업로드된 파일과 이름이 다르다면 retriever를 새로 생성하도록 flag 설정/ 버튼 flag 설정
            new_file_uploaded = st.session_state.get("pdf_file_name") != safe_file_name
            if new_file_uploaded:
                # flag 설정/ message initializer
                st.session_state["messages"] = []  # 기존 대화 내역 삭제
                st.session_state['run_chat_assistant'] = False
                st.session_state['run_llm_parser'] = False

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
            st.session_state['new_file_uploaded'] = new_file_uploaded
                        
            if new_file_uploaded or "documents" not in st.session_state:
                # PDF에서 불필요한 공백 및 점 제거 등 전처리 (필요에 따라 수정)
                doc_text_formatted = st.session_state["pdf_text"].replace('.', '')
                doc_text_formatted = "".join("".join(doc_text_formatted.split("\n")).split("        "))
                # 문서 splitter: 긴 텍스트를 청크로 분할
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,
                    chunk_overlap=100,
                    length_function=len,
                )
                texts = text_splitter.split_text(doc_text_formatted)
                documents = [Document(page_content=text) for text in texts]
                st.session_state['documents'] = documents
                
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
    
    embeddings_model = load_embeddings()
    main(embeddings_model)
    
