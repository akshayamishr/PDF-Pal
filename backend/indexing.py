import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from langchain_qdrant import QdrantVectorStore

load_dotenv()
api_key = os.getenv("API_KEY")

def indexing(file_name):
    print("Start indexing\n")
    pdf_path = Path(__file__).parent / "uploaded_pdfs" / file_name

    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    print("File loaded\n")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=400)
    split_docs = splitter.split_documents(docs)

    print(f"PDF loaded and split into {len(split_docs)} chunks.")


    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=api_key
        )

    vector_store = QdrantVectorStore.from_documents(
        documents=split_docs,
        url = "http://localhost:6333/",
        collection_name=file_name,
        embedding=embeddings
    )

    print("Indexing of the document has been done successfully")
