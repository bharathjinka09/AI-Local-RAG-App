# Local Qwen Document Search

A small local retrieval-augmented generation (RAG) prototype. It extracts text from a PDF, Word document, or text file, creates embeddings with Hugging Face, stores them in ChromaDB, and uses a local Ollama Qwen model to answer questions about the document.

## What You Need

- Windows PowerShell
- Python 3.10 or later
- [Ollama](https://ollama.com/) installed and available on your `PATH`
- Internet access for the first download of the Hugging Face embedding model

The project has no API keys or cloud services. The language model runs locally through Ollama.

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

This installs ChromaDB, LangChain, Hugging Face embedding support, PyMuPDF, `python-docx`, and their pinned dependencies.

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

## Index and Query a Document

With the virtual environment active and Ollama available:

```powershell
python .\document_loader.py
```

The script performs these steps:

1. Extracts text from the selected document.
2. Splits the text into 500-character chunks with a 50-character overlap.
3. Downloads `sentence-transformers/all-mpnet-base-v2` on the first run, then creates embeddings.
4. Stores embeddings in the `documents` collection under `chroma_db`.
5. Prompts for a search query.
6. Prints the three closest text chunks and two locally generated answers.

The first run can take a while because the embedding model must be downloaded. Later runs reuse its local Hugging Face cache.

## Reset Indexed Data

The Chroma database persists under `chroma_db`. Each script run adds the selected document's chunks to the existing `documents` collection.

To start with an empty index, stop the script and delete the database directory:

```powershell
Remove-Item -Recurse -Force .\chroma_db
```

Run `python .\document_loader.py` again to create a new database from the selected source document.

## Project Files

| File | Purpose |
| --- | --- |
| `document_loader.py` | Extracts documents, embeds text, stores it in ChromaDB, and answers questions using Qwen. |
| `test_qwen.py` | Supported smoke test for the local Ollama API. |
| `testQwen.py` | Experimental streaming request example. |
| `requirements.txt` | Pinned Python dependencies, encoded as UTF-16. |
| `sample.pdf`, `sample.docx`, `sample.txt` | Sample documents for testing. |
| `chroma_db/` | Locally generated persistent vector database; safe to delete to reset indexed data. |

## Troubleshooting

### `ollama` is not recognized

Reinstall Ollama or reopen PowerShell after installation. Confirm it is visible with:

```powershell
ollama --version
```

### Connection refused at port 11434

Start Ollama, or run `ollama serve` in a separate terminal, then rerun the Python command.

### `model 'qwen2.5:latest' not found`

Download it with:

```powershell
ollama pull qwen2.5:latest
```

### `Unsupported file format`

Check that `sample_file` points to an existing `.pdf`, `.docx`, or `.txt` file. File extensions are matched in lowercase.

### Dependency installation fails while reading `requirements.txt`

Use the PowerShell `Get-Content` command shown in [Install Python Dependencies](#install-python-dependencies), which explicitly reads the repository's UTF-16 dependency file.