import streamlit as st
import sys, os
import time
import pandas as pd
from langchain_community.vectorstores import FAISS


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from btt_parser import *

parser = Biollm(model = 'gemma2:27b')  # Assuming Biollm is a parser class you've defined


# Ensure session state keys exist
if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None

if "retriever" not in st.session_state:
    st.session_state.retriever = None

if "documents" not in st.session_state:
    st.session_state.documents = None

if "df_result" not in st.session_state:
    st.session_state.df_result = None

if "run_chat_assistant" not in st.session_state:
    st.session_state.run_chat_assistant = False

if "run_llm_parser" not in st.session_state:
    st.session_state.run_llm_parser = False

# Sidebar UI
with st.sidebar:
    st.title('📁 BTT Report Extractor')    
    # Display uploaded file info
    if st.session_state.pdf_path is not None:
        pdf_path = st.session_state.pdf_path
        st.sidebar.write(f"📄 **{os.path.basename(pdf_path)}** is ready.")
    else:
        st.sidebar.write("⚠️ No PDF file uploaded.")

    if st.button("🚀 Run LLM Parser"):
        if st.session_state.pdf_path is not None and st.session_state.run_llm_parser == False:
            
            with st.spinner("🔄 Running LLM Parser... Please wait..."):
                parser.run(st.session_state.pdf_path)  # Run the parser
                new_df = pd.DataFrame([parser.parsed_data])  # 새 데이터 프레임 생성

                # 기존 final_df가 존재하고, None이 아니며 비어있지 않으면 기존 데이터에 추가
                st.session_state.run_llm_parser = True
                
                if st.session_state['new_file_uploaded']:
                    st.session_state.df_result = pd.concat([st.session_state.df_result, new_df], ignore_index=True)
                else:
                    st.session_state.df_result = new_df

                parser.refresh()  # Reset parser state
            st.sidebar.success("✅ LLM Parser finished!")
        elif st.session_state.run_llm_parser == True:
            st.warning("⚠️ Please upload a new PDF file first.")
        
        else:
            st.sidebar.warning("⚠️ Please upload a PDF first.")

    # chatbot
    if st.button("Run Chat Assistant"):
        if st.session_state.documents is not None and st.session_state.run_chat_assistant == False:
            
            with st.spinner("🔄 Running Chat Assistant... Please wait..."):
                db = FAISS.from_documents(st.session_state['documents'], st.session_state["embeddings_model"])
                retriever = db.as_retriever(
                    search_type='mmr',
                    search_kwargs={'k': 4, 'fetch_k': 50, 'lambda_mult': 0.7})
                st.session_state.retriever = retriever
                st.session_state.run_chat_assistant = True

        elif st.session_state.run_chat_assistant == True:
            st.warning("⚠️ Please upload a new PDF file first.")        
        else:
            st.warning("⚠️ Please upload a PDF first.")

# Display extracted data if available
if st.session_state.df_result is not None:
    st.subheader("📊 Extracted Data")
    # Editable DataFrame
    edited_df = st.data_editor(st.session_state.df_result, num_rows="dynamic")
    st.session_state.df_result = edited_df  # Save changes in session state
    st.success("✅ Changes saved!")
    # CSV 다운로드 버튼 추가
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", csv, "extracted_data.csv", "text/csv")

if st.session_state.run_chat_assistant:
    st.subheader("🤖 Chat Assistant")
    # 세션에 chat history가 없다면 초기화
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    # 이전 대화 내역 표시
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    # 사용자 입력 받기
    if prompt := st.chat_input("Enter your question for the Chat Assistant"):
        # 사용자 메시지 추가
        st.session_state["messages"].append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 모델을 활용한 답변 생성 (예, parser.rag 사용)
        with st.chat_message("assistant"):
            # retriever와 사용자의 질문을 이용해 답변 생성
            response = parser.rag(st.session_state.retriever, prompt)
            st.markdown(response)
        # 어시스턴트의 응답을 chat history에 추가
        st.session_state["messages"].append({"role": "assistant", "content": response})
