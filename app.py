import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_ollama import OllamaLLM
from document_loader import process_document, store_embeddings

# Initialize FastAPI app
app = FastAPI()

# Load Qwen2.5 AI via Ollama
llm = OllamaLLM(model="qwen2.5:latest")

# Load the embeddings model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

# Define request model
class QueryRequest(BaseModel):
    query: str
    document_filename: Optional[str] = None


def get_document_context(query: str, document_filename: Optional[str] = None):
    vectorstore = Chroma(
        collection_name="documents",
        persist_directory="chroma_db",
        embedding_function=embedding_model,
    )
    if document_filename:
        source_path = os.path.abspath(os.path.join("uploaded_files", Path(document_filename).name))
        is_summary_request = any(word in query.lower() for word in ("summarize", "summary", "overview"))
        if is_summary_request:
            documents = vectorstore.get(where={"source": source_path}, include=["documents"])["documents"]
            return "\n\n".join(document for document in documents if document)

        documents = vectorstore.similarity_search(query, k=3, filter={"source": source_path})
    else:
        documents = vectorstore.similarity_search(query, k=3)

    return "\n\n".join(document.page_content for document in documents)


@app.post("/upload")
async def upload_and_index_document(file: UploadFile = File(...)):
    """Save a supported document and add its text chunks to ChromaDB."""
    filename = Path(file.filename or "").name
    if Path(filename).suffix.lower() not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, and TXT files are supported.")

    os.makedirs("uploaded_files", exist_ok=True)
    file_path = os.path.join("uploaded_files", filename)
    with open(file_path, "wb") as destination:
        destination.write(await file.read())

    texts = process_document(file_path)
    if not texts:
        raise HTTPException(status_code=400, detail="The uploaded document did not contain readable text.")

    store_embeddings(texts, file_path)
    return {"filename": filename, "chunks_indexed": len(texts)}


@app.post("/query")
def search_and_generate_response(request: QueryRequest):
    """Retrieve documents and generate AI-powered response"""
    context = get_document_context(request.query, request.document_filename)
    if not context:
        raise HTTPException(status_code=404, detail="No indexed text was found for the selected document.")

    document_name = request.document_filename or "the indexed documents"
    prompt = f"""Answer the user's question using only the document content below.
The user has already uploaded {document_name}; do not ask them to provide it again.
If the answer is not present in the content, say that clearly.

Document content:
{context}

Question: {request.query}
"""
    response = llm.invoke(prompt)
    return {"query": request.query, "response": response}

# Root endpoint
@app.get("/")
def home():
    return {"message": "Qwen AI-powered search API is running!"}





