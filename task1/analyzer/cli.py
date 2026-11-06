"""Read a document and emit JSON only after successful validation."""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from analyzer.extractor import ExtractionError, extract
from analyzer.schemas import SCHEMAS

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract invoices or resumes into validated JSON using Gemini.")
    parser.add_argument("kind", choices=SCHEMAS)
    parser.add_argument("input", type=Path, help="UTF-8 text file")
    parser.add_argument("--model", help="Override GEMINI_MODEL")
    args = parser.parse_args(argv)
    load_dotenv(ROOT / ".env")

    try:
        text = args.input.read_text(encoding="utf-8-sig")
        key = os.getenv("GEMINI_API_KEY", "").strip()
        if not key:
            raise ValueError("Set GEMINI_API_KEY in .env (copy .env.example first).")
        result = extract(text, args.kind, api_key=key,
                         model=args.model or os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"))
        payload = result.model_dump_json(indent=2) + "\n"
        sys.stdout.write(payload)
    except (OSError, UnicodeError):
        print("Error: Could not read UTF-8 input or print output. Check the path and permissions.", file=sys.stderr)
        return 1
    except (ValueError, ExtractionError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0
