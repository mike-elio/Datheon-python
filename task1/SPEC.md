# Document extraction

Build a small Python 3.12 CLI using Gemini to extract invoices and resumes
from UTF-8 text into strictly validated JSON. No web server or database.

Commands: `python main.py invoice examples/invoice.txt`,
`python main.py resume examples/cv.txt`, `python -m unittest discover -s tests -v`.

Keep schemas, prompts, API integration, and CLI in separate modules. Use typed
functions and Pydantic models rather than generic service layers. Support an
environment-based key and configurable model, with no embedded credentials.

Acceptance: schema-constrained Gemini requests; parameterized prompts with
examples; required nullable fields for absent facts; rejection of malformed JSON,
wrong types, extra fields, invalid dates, and nonfinite numbers. Print validated JSON
to stdout without file-saving options. Errors exit nonzero without exposing document content or API credentials.
Test both schemas and the request/CLI boundary offline with stubbed API responses.
Live extraction is verified separately after the user supplies a key.
