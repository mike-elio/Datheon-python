import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pydantic import ValidationError

from analyzer.schemas import SCHEMAS

ROOT = Path(__file__).resolve().parents[1]


def example(kind):
    return json.loads((ROOT / "examples" / f"{kind}.json").read_text(encoding="utf-8"))


class SchemaTests(unittest.TestCase):
    def test_examples_validate(self):
        for kind, schema in SCHEMAS.items():
            with self.subTest(kind=kind):
                schema.model_validate_json(json.dumps(example(kind)))

    def test_invoice_rejects_bad_values(self):
        for field, value in [("total", "115"), ("total", True),
                             ("total", float("nan")), ("issue_date", "2026-02-30"),
                             ("currency", "riyal"), ("extra", "unknown")]:
            with self.subTest(field=field, value=value):
                data = example("invoice")
                data[field] = value
                with self.assertRaises(ValidationError):
                    SCHEMAS["invoice"].model_validate_json(json.dumps(data))

    def test_required_keys_and_nested_extras(self):
        for kind, schema in SCHEMAS.items():
            data = example(kind)
            del data["warnings"]
            with self.assertRaises(ValidationError):
                schema.model_validate_json(json.dumps(data))
        data = example("resume")
        data["experience"][0]["secret"] = "extra"
        with self.assertRaises(ValidationError):
            SCHEMAS["resume"].model_validate_json(json.dumps(data))

    def test_rejects_markdown_and_wrong_document_type(self):
        for raw in ["```json\n{}\n```", "{}", json.dumps(example("resume"))]:
            with self.assertRaises(ValidationError):
                SCHEMAS["invoice"].model_validate_json(raw)

    def test_missing_facts_can_be_explicit_nulls(self):
        data = example("invoice")
        for key in data:
            if key not in ("document_type", "items", "warnings"):
                data[key] = None
        data["items"] = []
        self.assertIsNone(SCHEMAS["invoice"].model_validate_json(json.dumps(data)).total)

    def test_resume_rejects_invalid_nested_types(self):
        data = example("resume")
        data["experience"][0]["highlights"] = "not a list"
        with self.assertRaises(ValidationError):
            SCHEMAS["resume"].model_validate_json(json.dumps(data))


class ExtractionTests(unittest.TestCase):
    def test_prompt_examples_do_not_depend_on_input_files(self):
        from analyzer.prompts import EXAMPLES, build_instructions
        with patch("pathlib.Path.read_text", side_effect=FileNotFoundError):
            for kind in SCHEMAS:
                instructions = build_instructions(kind)
                self.assertIn("Worked example output:", instructions)
                SCHEMAS[kind].model_validate_json(EXAMPLES[kind][1])

    def test_both_paths_with_fake_gemini(self):
        from analyzer.extractor import extract
        for kind in SCHEMAS:
            with self.subTest(kind=kind), patch("analyzer.extractor.genai.Client") as client:
                api = client.return_value.__enter__.return_value
                api.models.generate_content.return_value = SimpleNamespace(
                    text=json.dumps(example(kind)),
                    candidates=[SimpleNamespace(finish_reason="STOP")],
                )
                result = extract("Sample document", kind, api_key="test", model="test-model")
                self.assertEqual(result.document_type, kind)
                request = api.models.generate_content.call_args.kwargs
                self.assertEqual(request["config"].response_mime_type, "application/json")
                self.assertIn("required", request["config"].response_json_schema)
                self.assertIn("Sample document", request["contents"])

    def test_invalid_or_incomplete_api_output_is_rejected(self):
        from analyzer.extractor import ExtractionError, extract
        for text, reason in [("{}", "STOP"), (None, "STOP"),
                             (json.dumps(example("invoice")), "MAX_TOKENS")]:
            with self.subTest(reason=reason, text=text), patch("analyzer.extractor.genai.Client") as client:
                api = client.return_value.__enter__.return_value
                api.models.generate_content.return_value = SimpleNamespace(
                    text=text, candidates=[SimpleNamespace(finish_reason=reason)])
                with self.assertRaises(ExtractionError):
                    extract("invoice", "invoice", api_key="test", model="test")

    def test_blank_document_is_rejected(self):
        from analyzer.extractor import extract
        with self.assertRaises(ValueError):
            extract("  ", "invoice", api_key="test", model="test")

    def test_transport_error_does_not_expose_secrets(self):
        from analyzer.extractor import ExtractionError, extract
        with patch("analyzer.extractor.genai.Client", side_effect=RuntimeError("secret-key")):
            with self.assertRaises(ExtractionError) as error:
                extract("private document", "invoice", api_key="secret-key", model="test")
        self.assertNotIn("secret-key", str(error.exception))


class CliTests(unittest.TestCase):
    def test_success_prints_validated_json(self):
        from analyzer.cli import main
        model = SCHEMAS["resume"].model_validate_json(json.dumps(example("resume")))
        output = io.StringIO()
        with patch("analyzer.cli.extract", return_value=model), patch.dict(
            "os.environ", {"GEMINI_API_KEY": "test"}
        ), redirect_stdout(output):
            self.assertEqual(main(["resume", str(ROOT / "examples/cv.txt")]), 0)
        self.assertEqual(json.loads(output.getvalue()), example("resume"))

    def test_failure_prints_no_json(self):
        from analyzer.cli import main
        from analyzer.extractor import ExtractionError
        output = io.StringIO()
        with patch("analyzer.cli.extract", side_effect=ExtractionError("Invalid output")), patch.dict(
            "os.environ", {"GEMINI_API_KEY": "test"}
        ), redirect_stderr(io.StringIO()), redirect_stdout(output):
            self.assertEqual(main(["invoice", str(ROOT / "examples/invoice.txt")]), 1)
        self.assertEqual(output.getvalue(), "")

    def test_missing_key_is_actionable(self):
        from analyzer.cli import main
        error = io.StringIO()
        with patch("analyzer.cli.load_dotenv"), patch.dict("os.environ", {}, clear=True), redirect_stderr(error):
            self.assertEqual(main(["invoice", str(ROOT / "examples/invoice.txt")]), 1)
        self.assertIn("GEMINI_API_KEY", error.getvalue())


if __name__ == "__main__":
    unittest.main()
