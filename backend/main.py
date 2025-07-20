from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import uvicorn
import shutil
import uuid
from indexing_graph import indexing
from retrieval_graph import chat
from pydantic import BaseModel

app = FastAPI()

UPLOAD_DIRECTORY = "uploaded_pdfs"

os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

@app.post("/uploadpdf/")
def upload_pdf(file: UploadFile = File(...)):
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    file_location = os.path.join(UPLOAD_DIRECTORY, file.filename)
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return JSONResponse(
            status_code=200,
            content={"message": f"Successfully uploaded {file.filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not upload file: {e}")
 
    
class FileRequest(BaseModel):
    file_name: str

@app.post("/chat_setup/")
def chat_setup(request: FileRequest):
    try:
        indexing(request.file_name)
        chat_id = str(uuid.uuid4())
        return JSONResponse(
            status_code=200,
            content={"message": "Successfully completed the file indexing", "chat_id":chat_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not complete the file indexing: {e}")


class ChatRequest(BaseModel):
    chat_id: str
    message:str
    file_name:str

@app.post("/chatting/")
async def chatting(request:ChatRequest):
    try:
        response = await chat(chat_id=request.chat_id, query=request.message, file_name=request.file_name)
        return JSONResponse(
                status_code=200,
                content={"message": response}
            )
    except Exception as e:
        raise HTTPException(status_code=301, detail=f"Could not generate the response: {e}") 


@app.get('/')
def hello():
    return JSONResponse(
        status_code=200,
        content={"message": "Hello World"}
    )


if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)
