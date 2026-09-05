import os
import hashlib
import pymupdf  # PyMuPDF for PDFs
import docx
import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_ollama import OllamaLLM
from langchain_classic.chains import RetrievalQA

# Load the LLM (Qwen) using Ollama
llm = OllamaLLM(model="qwen2.5:latest")

def search_and_summarize(query, db_path="chroma_db"):
    """Retrieve relevant documents and summarize them using Qwen AI"""
    
    # Load ChromaDB
    vectorstore = Chroma(collection_name="documents", persist_directory=db_path, embedding_function=embedding_model)
    
    # Create a LangChain Retrieval-QA pipeline
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

    # Get AI-generated answer
    response = qa_chain.invoke(query)

    print("\n💡 AI-Powered Answer:")
    print(response)



def generate_ai_response(context, query):
    """Send user query along with retrieved documents to Qwen AI for RAG"""
    prompt = f"""
    You are an AI assistant with access to the following information:
    
    {context}
    
    Based on this, answer the following question:
    {query}
    """
    
    payload = {"model": "qwen2.5:latest", "prompt": prompt, "stream": False}
    response = requests.post(OLLAMA_API_URL, json=payload)
    
    return response.json().get("response", "No response generated.")

def search_and_generate_response(query, db_path="chroma_db"):
    """Retrieve relevant documents and use Qwen AI for contextual response"""
    vectorstore = Chroma(collection_name="documents", persist_directory=db_path, embedding_function=embedding_model)
    results = vectorstore.similarity_search(query, k=3)  # Retrieve top 3 matches
    
    # Combine retrieved documents into context
    context = "\n\n".join([doc.page_content for doc in results])
    
    # Generate AI response using RAG
    ai_response = generate_ai_response(context, query)
    
    print("\n💡 AI-Powered Answer:")
    print(ai_response)


# Load the embeddings model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")


def process_document(file_path):
    """Extract text, split it, and convert to embeddings"""
    text = extract_text(file_path)
    
    if not text:
        return None

    # Split text into smaller chunks for better search performance
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_text(text)

    return texts

def store_embeddings(texts, source_path, db_path="chroma_db"):
    """Replace stored chunks for a source document with its current contents."""
    vectorstore = Chroma(collection_name="documents", persist_directory=db_path, embedding_function=embedding_model)
    source_id = os.path.abspath(source_path)
    document_ids = [
        hashlib.sha256(f"{source_id}:{index}:{text}".encode("utf-8")).hexdigest()
        for index, text in enumerate(texts)
    ]
    metadatas = [{"source": source_id} for _ in texts]

    try:
        vectorstore.delete(where={"source": source_id})
        vectorstore.add_texts(texts, metadatas=metadatas, ids=document_ids)
    except InvalidArgumentError as error:
        if "expecting embedding with dimension" not in str(error):
            raise

        print("Existing embeddings use a different dimension. Rebuilding the collection.")
        chromadb.PersistentClient(path=db_path).delete_collection("documents")
        vectorstore = Chroma(collection_name="documents", persist_directory=db_path, embedding_function=embedding_model)
        vectorstore.add_texts(texts, metadatas=metadatas, ids=document_ids)
    
    print("✅ Embeddings stored successfully!")


def search_documents(query, db_path="chroma_db"):
    """Search stored embeddings in ChromaDB"""
    vectorstore = Chroma(collection_name="documents", persist_directory=db_path, embedding_function=embedding_model)
    results = vectorstore.similarity_search(query, k=3)  # Retrieve top 3 matches
    
    for idx, result in enumerate(results):
        print(f"\n🔹 Result {idx + 1}:")
        print(result.page_content)

    return results

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file"""
    text = ""
    try:
        doc = pymupdf.open(pdf_path)
        for page in doc:
            text += page.get_text("text") + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text

def extract_text_from_word(doc_path):
    """Extract text from a Word (.docx) file"""
    text = ""
    try:
        doc = docx.Document(doc_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error reading Word file {doc_path}: {e}")
    return text

def extract_text_from_txt(txt_path):
    """Extract text from a TXT file"""
    text = ""
    try:
        with open(txt_path, "r", encoding="utf-8") as file:
            text = file.read()
    except Exception as e:
        print(f"Error reading TXT file {txt_path}: {e}")
    return text

def extract_text(file_path):
    """Detect file type and extract text accordingly"""
    if file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith(".docx"):
        return extract_text_from_word(file_path)
    elif file_path.endswith(".txt"):
        return extract_text_from_txt(file_path)
    else:
        print(f"Unsupported file format: {file_path}")
        return ""

# Example usage
if __name__ == "__main__":
    sample_file = "sample.docx"
    texts = process_document(sample_file)
    if texts:
        store_embeddings(texts, sample_file)

    user_query = input("Enter your search query: ")
    results = search_documents(user_query)
    search_and_generate_response(user_query)
    search_and_summarize(user_query)


# # Example usage
# if __name__ == "__main__":
#     sample_pdf = "sample.pdf"
#     sample_doc = "sample.docx"
#     sample_txt = "sample.txt"
#     print(extract_text(sample_pdf))
#     print(extract_text(sample_doc))
#     print(extract_text(sample_txt))






