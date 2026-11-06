# Datheon Python

Task 1 extracts invoice and resume data from UTF-8 text using Gemini, then validates
the JSON with Pydantic. Results print to the terminal.

## Setup

Requires Python 3.12 or later. Run in PowerShell from the repository root:

```powershell
cd task1
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Add your [Gemini API key](https://aistudio.google.com/apikey) to `task1/.env`:

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

## Run

From `task1` with the virtual environment activated:

```powershell
python main.py resume examples/cv.txt
python main.py invoice examples/invoice.txt
```

Replace the example path with your own UTF-8 text file. Extract text from PDFs,
Word documents, or images before using them. Document text is sent to Google.

Resume example: [input](task1/examples/cv.txt) → [output](task1/examples/resume.json).
Invoice example: [input](task1/examples/invoice.txt) → [output](task1/examples/invoice.json).

## Code and tests

`task1/analyzer/` contains the schemas, prompt templates, Gemini client, and CLI.
Validation rejects extra fields, incorrect types, and malformed JSON. Missing facts
use `null` or empty lists. Schema validation does not guarantee factual accuracy.
API keys and virtual environments are excluded from Git.

Run the offline tests from `task1`:

```powershell
python -m unittest discover -s tests -v
```
