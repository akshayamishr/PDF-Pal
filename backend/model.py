from dotenv import load_dotenv
import os
from google import genai
from google.genai import types
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

def get_config(system_prompt,response_schema, thinking_config):
    if thinking_config:
        config = types.GenerateContentConfig(
            system_instruction = system_prompt,
            response_mime_type="application/json",
            response_schema=response_schema,
            thinking_config=types.ThinkingConfig(thinking_budget=0)
        )

    else:
        config = types.GenerateContentConfig(
            system_instruction = system_prompt,
            response_mime_type="application/json",
            response_schema=response_schema,
        )

    return config

def start_chat(model,messages,config):
    if(model == None):
       model = "gemini-1.5-flash"

    response = client.models.generate_content(
        model = model,
        contents = messages,
        config = config
    )
    return response

def get_response(query, model, config):
    response = client.models.generate_content(
        model = model, 
        contents = query,
        config = config
    )
    return response

# Vector Embeddings
embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=api_key
    )
