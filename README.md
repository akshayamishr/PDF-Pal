# PDF-Pal
- This is a simple web app that lets you upload a PDF file and chat with it. 
- Built using the Retrieval-Augmented Generation (RAG) architecture powered by **LangChain**, **FastAPI**, **Qdrant**, and **Streamlit**.
---

## 📜 Features
- 📂 Upload any PDF document
- 💬 Ask questions based on its content
- 🔍 Retrieval-Augmented Generation pipeline for accurate answers
- 🔄 Persistent chat session using unique `chat_id`
- ⚡ Real-time response with Streamlit UI
---

## 🧱 Tech Stack
- **Frontend:** Streamlit
- **Backend API:** FastAPI
- **LLM & Embeddings:** Google Gemini
- **Vector Database:** Qdrant
- **PDF Processing & Chunking:** LangChain
---

## 🔄 RAG Pipeline Overview
1. **Document Upload**: User uploads a PDF via Streamlit UI.
2. **Chunking & Embedding**:
   - The PDF is split into chunks using LangChain’s `RecursiveCharacterTextSplitter`.
   - Chunks are converted to embeddings using GoogleGenerativeAIEmbeddings.
3. **Vector Storage**:
   - The vector representations are stored in Qdrant.
4. **Query Handling**:
   - When a user asks a question, the app performs a similarity search in Qdrant.
   - Relevant chunks (context) are passed to the LLM in a system prompt.
5. **Answer Generation**:
   - The LLM generates a response grounded in the document’s content.
---

## 🏗️ System Architecture
```mermaid
graph TD
    A[User Uploads PDF via Streamlit] --> B[Streamlit Frontend]
    B -->|Send file| C[FastAPI Backend]
    C -->|Loads PDF| D[LangChain Loader]
    D --> E[Text Chunking & Embedding]
    E --> F[Qdrant Vector Store]

    G[User Query via Streamlit] --> H[FastAPI /chatting Endpoint]
    H --> I[Search Qdrant for Relevant Chunks]
    I --> J[Construct Context Prompt]
    J --> K[LLM Response Generation]
    K --> L[Return Answer to Frontend]
````
---

## 📬 Feedback & Contributions
Feel free to create issues or pull requests if you have ideas, spot bugs, or want to help improve the project!
