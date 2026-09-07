# Local Qwen Document Search

A small retrieval-augmented generation (RAG) prototype. It extracts text from a PDF, Word document, or text file, stores embeddings in ChromaDB, and uses a local Ollama Qwen model to answer questions about the document.

Two loader implementations are available:

- `document_loader.py` creates semantic embeddings with Hugging Face's `sentence-transformers/all-mpnet-base-v2`. This is the recommended option when internet access or a pre-populated Hugging Face cache is available.
- `document_loader_offline.py` creates deterministic local hash embeddings in Python. It works without internet access or Ollama embedding support, but retrieval is based primarily on matching words rather than semantic meaning.

## What You Need

- Windows PowerShell
- Python 3.10 or later
- [Ollama](https://ollama.com/) installed and available on your `PATH`

The language model runs locally through Ollama. The semantic loader downloads its embedding model from Hugging Face on its first run; the offline loader has no runtime network dependency for embeddings.

## Clone the Repository

```powershell
git clone <repository-url>
Set-Location <repository-folder>
```

Replace `<repository-url>` and `<repository-folder>` with the repository's actual values.

## Create and Activate a Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script, allow scripts for the current terminal session and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Your prompt should now begin with `(venv)`.

## Install Python Dependencies

The dependency file is UTF-16 encoded. `pip` may not reliably read that encoding directly, so use PowerShell to pipe its content to `pip`:

```powershell
Get-Content .\requirements.txt -Encoding Unicode | python -m pip install -r -
```

This installs ChromaDB, LangChain, Hugging Face embedding support, PyMuPDF, `python-docx`, and their pinned dependencies. Downloading and installing dependencies requires internet access unless packages are already available locally.

## Install and Prepare Ollama

1. Install Ollama from [ollama.com](https://ollama.com/), then reopen PowerShell so the `ollama` command is available.
2. Download the model used by this project:

   ```powershell
   ollama pull qwen2.5:latest
   ```

3. Confirm Ollama can run the model:

   ```powershell
   ollama run qwen2.5:latest "What is AI?"
   ```

Ollama normally starts its local API automatically at `http://localhost:11434`. Keep Ollama running while using the scripts.

## Verify Ollama Access

Run the non-streaming smoke test:

```powershell
python .\test_qwen.py
```

It sends `What is AI?` to `qwen2.5:latest` through Ollama and prints the response. Run this before troubleshooting the document workflow.

`testQwen.py` is an experimental streaming variant. Its current code requests streaming output but then parses the response as one JSON object, so use `test_qwen.py` for the supported verification path.

## Run the API

Start the FastAPI service in a separate PowerShell terminal:

```powershell
uvicorn app:app --reload
```

The service listens at `http://127.0.0.1:8000` by default and uses the semantic embeddings stored in `chroma_db`. It exposes these endpoints:

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | Confirms that the API is running. |
| `POST` | `/upload` | Accepts a multipart `file` field containing a PDF, DOCX, or TXT document, saves it, and indexes its chunks in `chroma_db`. |
| `POST` | `/query` | Retrieves the three closest chunks for questions, or all chunks for summary requests, from the requested uploaded document and returns a Qwen-generated answer. |

`POST /upload` returns the sanitized filename and number of indexed chunks. For example:

```json
{
   "filename": "my-document.pdf",
   "chunks_indexed": 12
}
```

To send the included example request while the API is running:

```powershell
python .\test_query.py
```

The endpoint expects a JSON body with a `query` value. Include `document_filename` from the upload response to restrict retrieval to that uploaded document and avoid answers based on older files in the shared collection. Requests containing `summarize`, `summary`, or `overview` use every indexed chunk from the selected document. For example:

```json
{
   "query": "What does the document say about AI?",
   "document_filename": "my-document.pdf"
}
```

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## Run the Web UI

The Streamlit interface requires the FastAPI service to be running. Start the API in one terminal:

```powershell
uvicorn app:app --reload
```

In a second terminal, start the UI:

```powershell
streamlit run .\app_ui.py
```

Open the local URL printed by Streamlit, typically `http://localhost:8501`. Upload a `.pdf`, `.docx`, or `.txt` file from the sidebar. The UI sends it to the API, which saves it under `uploaded_files/` and indexes its contents in the semantic `chroma_db` collection.

After indexing completes, the UI shows the active filename in the sidebar. Each question is filtered to that file's chunks, so a request to summarize the document uses the current upload rather than data from previously indexed files. Summary and overview requests use all indexed chunks for the active document; other questions use the three most relevant chunks. Uploading a different file makes it the active document for later questions in that browser session.

## Choose a Source Document

`document_loader.py` supports these extensions:

- `.pdf`
- `.docx`
- `.txt`

The repository includes `sample.pdf`, `sample.docx`, and `sample.txt` for local experimentation. Open `document_loader.py` and set the `sample_file` value in the `if __name__ == "__main__":` block to the document you want to index. For example:

```python
sample_file = "sample.txt"
```

Use a relative file name for a document in the repository root, or provide a relative/absolute path to another supported document.

## Choose a Loader

Use one loader at a time for a given document workflow.

| Loader | Embedding method | Internet needed at runtime | Database directory | Duplicate handling |
| --- | --- | --- | --- | --- |
| `document_loader.py` | Hugging Face `all-mpnet-base-v2` semantic embeddings | Yes, only if the model is not already cached | `chroma_db` | Replaces previous chunks from the selected source |
| `document_loader_offline.py` | 384-dimension local feature-hashing embeddings | No | `chroma_db_offline` | Replaces previous chunks from the selected source |

Do not point both loaders at the same Chroma directory. The semantic loader produces 768-dimension vectors, while the offline loader produces 384-dimension vectors. Chroma collections cannot mix vector dimensions.

## Index and Query a Document

With the virtual environment active and Ollama available:

```powershell
python .\document_loader.py
```

To run completely offline instead:

```powershell
python .\document_loader_offline.py
```

Both scripts perform these steps:

1. Extracts text from the selected document.
2. Splits the text into 500-character chunks with a 50-character overlap.
3. Creates embeddings using the selected loader's method.
4. Stores embeddings in the `documents` collection under that loader's database directory.
5. Prompts for a search query.
6. Prints the three closest text chunks and two locally generated answers.

On the semantic loader's first run, Hugging Face downloads `sentence-transformers/all-mpnet-base-v2`; later runs use the local Hugging Face cache. The offline loader does not download an embedding model.

## Reset Indexed Data

The semantic loader persists data under `chroma_db`. It uses stable IDs and source metadata, replacing old chunks from the selected document rather than creating duplicates.

The offline loader persists data under `chroma_db_offline`. It uses stable IDs and source metadata, replacing old chunks from the selected document rather than creating duplicates.

To start with an empty index, stop the script and delete the database directory:

```powershell
Remove-Item -Recurse -Force .\chroma_db
```

For the offline loader, reset its separate database with:

```powershell
Remove-Item -Recurse -Force .\chroma_db_offline
```

Run the relevant loader again to create a new database from the selected source document.

## Project Files

| File | Purpose |
| --- | --- |
| `app.py` | FastAPI service that accepts and indexes uploaded documents in the semantic Chroma index, then generates document-scoped answers with the local Ollama Qwen model. |
| `app_ui.py` | Streamlit web interface that uploads documents for ChromaDB indexing and sends questions to the FastAPI `/query` endpoint. |
| `document_loader.py` | Semantic RAG loader using the Hugging Face `all-mpnet-base-v2` embedding model. |
| `document_loader_offline.py` | Fully offline RAG loader using deterministic local feature-hashing embeddings and duplicate-safe indexing. |
| `test_qwen.py` | Supported smoke test for the local Ollama API. |
| `testQwen.py` | Experimental streaming request example. |
| `test_query.py` | Example client that posts a document question to the local FastAPI `/query` endpoint. |
| `requirements.txt` | Pinned Python dependencies, encoded as UTF-16. |
| `sample.pdf`, `sample.docx`, `sample.txt` | Sample documents for testing. |
| `chroma_db/` | Persistent vector database for the semantic loader; safe to delete to reset indexed data. |
| `chroma_db_offline/` | Persistent vector database for the offline loader; safe to delete to reset indexed data. |
| `uploaded_files/` | Files submitted through the Streamlit upload control and indexed in the semantic ChromaDB collection. |

## Troubleshooting

### `ollama` is not recognized

Reinstall Ollama or reopen PowerShell after installation. Confirm it is visible with:

```powershell
ollama --version
```

### Connection refused at port 11434

Start Ollama, or run `ollama serve` in a separate terminal, then rerun the Python command.

### Hugging Face asks for a token or fails without internet

Use `document_loader_offline.py`. It does not download or call a Hugging Face embedding model. Alternatively, run the semantic loader once while connected to allow `all-mpnet-base-v2` to be cached locally.

### `Collection expecting embedding with dimension ...`

Reset the database used by the active loader. This occurs when a Chroma directory contains vectors created by another embedding implementation.

### `model 'qwen2.5:latest' not found`

Download it with:

```powershell
ollama pull qwen2.5:latest
```

### `Unsupported file format`

Check that `sample_file` points to an existing `.pdf`, `.docx`, or `.txt` file. File extensions are matched in lowercase.

### Dependency installation fails while reading `requirements.txt`

Use the PowerShell `Get-Content` command shown in [Install Python Dependencies](#install-python-dependencies), which explicitly reads the repository's UTF-16 dependency file.
