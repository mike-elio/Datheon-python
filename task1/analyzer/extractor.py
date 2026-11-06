"""One Gemini request followed by strict local validation."""

from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from analyzer.prompts import build_instructions
from analyzer.schemas import SCHEMAS, Invoice, Resume


class ExtractionError(Exception):
    """A safe error message that never includes the document or credentials."""


def extract(text: str, kind: str, *, api_key: str, model: str) -> Invoice | Resume:
    if kind not in SCHEMAS:
        raise ValueError("Document type must be invoice or resume.")
    if not text.strip():
        raise ValueError("The input document is empty.")
    if len(text) > 100_000:
        raise ValueError("Document exceeds the 100,000 character limit. Split it first.")
    if not api_key.strip() or not model.strip():
        raise ValueError("GEMINI_API_KEY and GEMINI_MODEL must not be empty.")

    schema = SCHEMAS[kind]
    instructions = build_instructions(kind)
    try:
        with genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=90_000)) as client:
            response = client.models.generate_content(
                model=model,
                contents=text,
                config=types.GenerateContentConfig(
                    system_instruction=instructions,
                    response_mime_type="application/json",
                    response_json_schema=schema.model_json_schema(),
                ),
            )
    except errors.APIError as exc:
        raise ExtractionError(
            f"Gemini request failed (HTTP {exc.code}). Check the key, model, quota and access."
        ) from None
    except Exception:
        # SDK/transport exceptions may contain URLs, credentials or request text.
        raise ExtractionError("Could not contact Gemini. Check network and SDK configuration.") from None

    if not response.candidates or response.candidates[0].finish_reason != "STOP":
        raise ExtractionError("Gemini did not complete the response (blocked or truncated).")
    if not response.text:
        raise ExtractionError("Gemini returned an empty response.")
    try:
        return schema.model_validate_json(response.text)
    except ValidationError as exc:
        count = exc.error_count()
        raise ExtractionError(
            f"Gemini returned invalid JSON or schema data ({count} validation errors)."
        ) from None
