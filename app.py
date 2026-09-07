from fastapi import FastAPI
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.chains import RetrievalQA

from langchain_ollama import OllamaLLM

# Initialize FastAPI app
app = FastAPI()

# Load Qwen2.5 AI via Ollama
llm = OllamaLLM(model="qwen2.5:latest")

# Load the embeddings model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

# Load ChromaDB
vectorstore = Chroma(collection_name="documents", persist_directory="chroma_db", embedding_function=embedding_model)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

# Define request model
class QueryRequest(BaseModel):
    query: str

@app.post("/query")
def search_and_generate_response(request: QueryRequest):
    """Retrieve documents and generate AI-powered response"""
    response = qa_chain.invoke(request.query)
    return {"query": request.query, "response": response}

# Root endpoint
@app.get("/")
def home():
    return {"message": "Qwen AI-powered search API is running!"}





