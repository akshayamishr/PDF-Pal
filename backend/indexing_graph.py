import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from dotenv import load_dotenv
from langchain_qdrant import QdrantVectorStore
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from model import embeddings as embeddings

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

class State(TypedDict):
    file_name: str
    file_path: str
    loaded_docs: list | None
    splited_docs: list | None

def file_loader(state:State):
    pdf_path = state["file_path"]

    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    state["loaded_docs"] = docs

    return state

def file_splitter(state: State):
    docs = state["loaded_docs"]

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=400)
    split_docs = splitter.split_documents(docs)
    state['splited_docs'] = split_docs

    return state

def vector_embedder(state:State):
    file_name = state['file_name']
    split_docs = state['splited_docs']

    vector_store = QdrantVectorStore.from_documents(
        documents = split_docs,
        url = "http://localhost:6333/",
        collection_name=file_name,
        embedding=embeddings
    )

    return state

graph_builder = StateGraph(state_schema = State)

graph_builder.add_node("file_loader", file_loader)
graph_builder.add_node("file_splitter", file_splitter)
graph_builder.add_node("vector_embedder", vector_embedder)

graph_builder.add_edge(START, "file_loader")
graph_builder.add_edge("file_loader", "file_splitter")
graph_builder.add_edge("file_splitter", "vector_embedder")
graph_builder.add_edge("vector_embedder", END)

graph = graph_builder.compile()

def indexing(file_name):
    pdf_path = Path(__file__).parent / "uploaded_pdfs" / file_name
    
    state = State(
        file_name = file_name,
        file_path = pdf_path,
        loaded_docs = None,
        splited_docs = None,
    )
    graph.invoke(state)
    
    print("Indexing of the document has been done successfully")