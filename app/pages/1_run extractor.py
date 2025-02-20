import streamlit as st
import sys, os
import time
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from btt_parser import *

parser = Biollm()  # Assuming Biollm is a parser class you've defined

# Ensure session state keys exist
if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None

if "df_result" not in st.session_state:
    st.session_state.df_result = None

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
        if st.session_state.pdf_path is not None:
            with st.spinner("🔄 Running LLM Parser... Please wait..."):
                parser.run(st.session_state.pdf_path)  # Run the parser
                new_df = pd.DataFrame([parser.parsed_data])  # 새 데이터 프레임 생성
                
                # 기존 final_df가 존재하고, None이 아니며 비어있지 않으면 기존 데이터에 추가
                if ('final_df' in st.session_state 
                    and st.session_state.final_df is not None 
                    and not st.session_state.final_df.empty):
                    st.session_state.df_result = pd.concat([st.session_state.final_df, new_df], ignore_index=True)
                else:
                    st.session_state.df_result = new_df

                parser.refresh()  # Reset parser state
            st.sidebar.success("✅ LLM Parser finished!")
        else:
            st.sidebar.warning("⚠️ Please upload a PDF first.")

# Display extracted data if available
if st.session_state.df_result is not None:
    st.subheader("📊 Extracted Data")
    # Editable DataFrame
    edited_df = st.data_editor(st.session_state.df_result, num_rows="dynamic")
    st.session_state.df_result = edited_df  # Save changes in session state
    st.success("✅ Changes saved!")
    
    st.session_state['final_df'] = st.session_state.df_result

    # CSV 다운로드 버튼 추가
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", csv, "extracted_data.csv", "text/csv")

      
# if st.session_state.df_result is not None:
# # 세션 상태에서 df_result가 없으면 초기화
#     if "df_result" not in st.session_state:
#         st.session_state.df_result = pd.DataFrame()  # 빈 데이터프레임 생성

    
#     st.subheader("📊 Extracted Data")
#     # 수정 가능한 DataFrame 표시    
#     st.dataframe(st.session_state.df_result)  # Display DataFrame
#     st.success("✅ Changes saved in session state!")
    
#     st.session_state['final_df'] = st.session_state.df_result
#     # # CSV 다운로드 버튼 추가
#     csv = st.session_state.df_result.to_csv(index=False).encode('utf-8')
#     st.download_button("📥 Download CSV", csv, "edited_data.csv", "text/csv")
