from dotenv import load_dotenv
import os
from langchain_qdrant import QdrantVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from google import genai
from google.genai import types
from pydantic import BaseModel
import json
from database import save_message,load_chat_history

load_dotenv()
api_key = os.getenv("API_KEY")
client = genai.Client(api_key=api_key)

# Vector Embeddings
embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=api_key
    )

class responseStruture(BaseModel):
    content : str

def get_config(system_prompt):
    config = types.GenerateContentConfig(
    system_instruction = system_prompt,
    response_mime_type="application/json",
    response_schema=responseStruture
    )
    return config

def getResponse(messages,config):
        response = client.models.generate_content(
        model = "gemini-2.0-flash",
        contents = messages,
        config = config
        )
        return response

def chat(chat_id, user_prompt, file_name):

    save_message(chat_id=chat_id,role="user",message=user_prompt)

    vector_db = QdrantVectorStore.from_existing_collection(
    url="http://localhost:6333",
    collection_name=file_name,
    embedding=embeddings
    )
    search_results = vector_db.similarity_search(query=user_prompt)

    context = "\n\n\n".join([f"Page Content: {result.page_content}\nPage Number: {result.metadata['page_label']}\nFile Location: {result.metadata['source']}" for result in search_results])
    SYSTEM_PROMPT = f"""
        You are a helpful and knowledgeable AI assistant that answers user questions using only the provided context from a PDF document.

        The context includes content from the document along with their corresponding page numbers. Your goal is to provide accurate, concise, and relevant answers strictly based on this context. 

        If the answer is not explicitly present in the context, politely inform the user that the information is not available in the document.

        When helpful, guide the user to the correct page number so they can explore further.

        Use the following context to answer:

        {context}
        """

    chat_history = load_chat_history(chat_id=chat_id)
    config = get_config(SYSTEM_PROMPT)
    response = getResponse(messages=chat_history,config=config)

    parsed_response = json.loads(response.text)

    return parsed_response.get("content")
