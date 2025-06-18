import streamlit as st
from streamlit import session_state as ss
import chat
import requests

if "page" not in st.session_state:
    ss.page = "home"

if "chat_id" not in ss:
    ss.chat_id = ""

def go_to_chat():
    ss.page = "chat"

if st.session_state.page == "home":
    st.title("RAG App to chat with any :red[PDF]")

    st.write("Your PDF AI - ask questions to any PDF and stay ahead.")

    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    if uploaded_file:
        ss["pdf_file"] = uploaded_file
        if(uploaded_file):
        # FastAPI backend URL
            FASTAPI_URL = "http://127.0.0.1:8000/uploadpdf/"

            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}

                response = requests.post(FASTAPI_URL, files=files)

                if response.status_code == 200:
                    st.success(f"File uploaded successfully! Response from backend: {response.json()}")
                else:
                    st.error(f"Error uploading file: {response.status_code} - {response.json()}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

        start_indexing = st.button("Start file indexing")
        if(start_indexing):
            try:
                FASTAPI_URL = f"http://127.0.0.1:8000/chat_setup/"
                response = requests.post(FASTAPI_URL,json={"file_name": uploaded_file.name})

                if response.status_code  == 200:
                    st.success("Chat setup has been done successfully")
                    ss.chat_id = response.json().get("chat_id")
                else:
                    st.error(f"Error unable to start indexing.")

            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

            start_chatting = st.button("Start chatting with the pdf",on_click= go_to_chat)


elif st.session_state.page == "chat":
    chat.chat()
