import streamlit as st
from streamlit import session_state as ss
import requests

def chat():
    st.title("💬 PDF Chatbot")

    if 'pdf_file' in ss:
        st.write(ss['pdf_file'].name)

    if "chat_history" not in ss:
        ss.chat_history = []

    for role, message in st.session_state.chat_history:
        if role == "user":
            st.chat_message("user").markdown(message)
        else:
            st.chat_message("assistant").markdown(message)

    # User input
    user_input = st.chat_input("Type your question here...")
    if user_input:
        ss.chat_history.append(("user", user_input))
        st.chat_message("user").markdown(user_input)

        try:
            FASTAPI_URL = "http://127.0.0.1:8000/chatting/"
            payload = {
                "chat_id": ss.chat_id,     
                "message": user_input,
                "file_name": ss['pdf_file'].name
            }

            res = requests.post(FASTAPI_URL, json=payload)

            if res.status_code == 200:
                response = res.json().get("message", "No response")
            else:
                response = f" Error {res.status_code}: {res.text}"

        except Exception as e:
            response = f" Exception: {str(e)}"

        ss.chat_history.append(("assistant", response))
        st.chat_message("assistant").markdown(response)
        print(ss.chat_history)
